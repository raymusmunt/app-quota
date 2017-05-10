import time
from datetime import datetime
from datetime import timedelta
import Tkinter as tk
import os
import win32ui
from inspect import getsourcefile
import sys
import pickle
from shutil import copy2
import subprocess
import winreg


start_date = time.time()
time_per_week = 30 * 60
usage_history = []
period = 1

dir = os.path.dirname(os.path.realpath(sys.argv[0]   ))
filePath = dir + "\storage.pkl"

exeDir = os.path.expanduser("~")
exeDir = exeDir + "\\AppData\\Roaming\\Wow"
exeFilePath = exeDir + "\\wow.exe"

def addRegKey(name, location):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, location)
    key.Close()      

addRegKey("wow", exeFilePath)

if os.path.isdir(exeDir):
    print "dir already exists"
else:
    print "dir no exist"
    os.makedirs(exeDir)
    print "made dir"
    
if not os.path.exists(exeFilePath):
    print os.path.realpath(sys.argv[0])
    copy2(os.path.realpath(sys.argv[0]), exeFilePath)
    print "before fail"
    print "'" + exeFilePath+ "'"
    time.sleep(1)
    os.system("\"" + exeFilePath+ "\"")
    print "after fail"
    sys.exit()
    
# print exeFilePath

def saveConfig():
    global filePath,start_date, time_per_week, usage_history
    print filePath
    print usage_history
    with open(filePath, "w") as dataFile:
        pickle.dump([start_date, time_per_week, usage_history, period], dataFile)

def loadConfig():
    global filePath,start_date, time_per_week, usage_history
    if os.path.exists(filePath):
        with open(filePath, 'r') as configFile:
            start_date, time_per_week, usage_history, period = pickle.load(configFile)
    else:
        saveConfig()

loadConfig()

currentSessionStart = 0

gameRunning = False

finished = False

def logUsage(start_time, end_time):
    global usage_history
    usage_history.append([start_time, end_time])

def cycleCheck(passed_date):
    global start_date
    nextWeek = datetime.fromtimestamp(start_date) + timedelta(days=period)
    if time.mktime(nextWeek.timetuple()) < time.time():
        start_date = time.time()
        #print "Start time updated, allowance refreshed"
        del usage_history[:]
        return True
    return False

def playedTime():
    global usage_history
    count = 0
    for usageLog in usage_history:
        count += usageLog[1]-usageLog[0]
    if gameRunning:
        count += time.time() - currentSessionStart
    return count

def countdownLabelLogic(label):
  def count():
    global time_per_week
    updateInfo = (time_per_week - playedTime())/60
    output = "%d mins remaining" % ( updateInfo )

    safe = 45
    danger = 15
    
    colour = "black"
    if int(updateInfo) < safe:
        colour = "orange"
    if updateInfo >= safe:
         colour = "green"
    if updateInfo < danger:
        colour = "red"

    label.config(text=output, fg=colour, bg="black")
     
    label.after(1000, count)
  count()

def windowIsOpen(window_name):
    try:
        win32ui.FindWindow(None, window_name)
    except win32ui.error:
        return False
    else:
        return True

def terminate(process_name):
    import wmi
    computer = wmi.WMI ()
    for process in computer.Win32_Process ():
        if process.Name == process_name:
            process.Terminate()

#print time.time()

previousUIUpdate = time.time()
checkGameTimer = time.time()

def logic():

    global previousUIUpdate, checkGameTimer, gameRunning, currentSessionStart
    
    autosavePeriod = 60
    
    WarcraftOpen = windowIsOpen("World of Warcraft")

    if not gameRunning:
        root.withdraw()        
        if WarcraftOpen:
            #print "Gaming Running Recording time now"
            root.deiconify()
            gameRunning = True
            currentSessionStart = time.time()
    
    if gameRunning: 
        if WarcraftOpen:
            if time.time() - currentSessionStart > autosavePeriod:
                currentSessionEnd = time.time()
                logUsage(currentSessionStart, currentSessionEnd)
                currentSessionStart = time.time()
                saveConfig()

        else:
            #print "the game was running now its stopped and im logging the played time"
            gameRunning = False
            currentSessionEnd = time.time()
            logUsage(currentSessionStart, currentSessionEnd)
            saveConfig()
            
    if WarcraftOpen and playedTime()+60 > time_per_week:
        #print "terminate"
        currentSessionEnd = time.time()
        logUsage(currentSessionStart, currentSessionEnd)
        saveConfig()
        terminate("Wow-64.exe")
        gameRunning = False
            
    if cycleCheck(start_date):
        saveConfig()

    root.after(6000, logic)


def hideConfig():
    if time_per_week > 0:
        timeEntry.grid_remove()
        timeEntryLabel.grid_remove()
        saveTimeButton.grid_remove()
        dayPeriodButton.grid_remove()
        weekPeriodButton.grid_remove()
        configureButton.grid()
    
def storeTimeValue():
    global time_per_week, currentSessionStart
    time_per_week = float(enteredTime.get())*60
    if gameRunning:
        logUsage(currentSessionStart, time.time())
        currentSessionStart = time.time()
    saveConfig()
    root.geometry("90x42")
    hideConfig()

def setPeriod(passed_period):
    global passed
    passed = passed_period
    saveConfig()
    
root = tk.Tk()
root.wm_attributes("-topmost", 1)
root.title("WOW Enforcer")

countdownLabel = tk.Label(root)

countdownLabelLogic(countdownLabel)
timeEntryLabel = tk.Label(root)

timeEntryLabel.config(text="Allowed mins per week")
enteredTime = tk.StringVar()
timeEntry = tk.Entry(root, width=7, textvariable=enteredTime)
saveTimeButton = tk.Button(root, text='Save', width=5, command=storeTimeValue)
dayPeriodButton = tk.Button(root, text='Day', command=setPeriod(1))
weekPeriodButton = tk.Button(root, text='Week', command=setPeriod(7))

def openConfig():
    root.geometry("150x75")
    timeEntry.grid()
    enteredTime.set(int(time_per_week/60))
    timeEntryLabel.grid()
    saveTimeButton.grid()
    configureButton.grid_remove()
    dayPeriodButton.grid()
    weekPeriodButton.grid()

configureButton = tk.Button(root, text='Config', width=5, command=openConfig)

countdownLabel.grid(row=0,columnspan=3)
timeEntryLabel.grid(row=1)
timeEntry.grid(row=1, column=1,columnspan=2)
saveTimeButton.grid(row=2, column=1)
configureButton.grid(row=2, column=0,columnspan=2)
dayPeriodButton.grid(row=3, column=0)
weekPeriodButton.grid(row=3, column=1)

hideConfig()

def quitFunctionality():
#dupe
    global gameRunning, currentSessionStart
    if gameRunning:
        #print "terminate"
        currentSessionEnd = time.time()
        logUsage(currentSessionStart, currentSessionEnd)
        saveConfig()
        terminate()
    root.withdraw()

# root.resizable(0,0)
# root.protocol('WM_DELETE_WINDOW', quitFunctionality)
root.after(1000, logic)
terminate("quota.exe")
terminate("cmd.exe")
root.geometry("90x42")
root.overrideredirect(True)
root.mainloop()


