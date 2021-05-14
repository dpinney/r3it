from ..logger import *
from shutil import copy2 as copy
from os.path import join
import os, pytest

# define constants
testDir = os.path.dirname(os.path.abspath(__file__))
logName = join(testDir,'..','data','log.txt')
logSaveName = join(testDir,'..','data','logSave.txt')
message = 'test'
    
# save out the log before our tests make changes to it
def setup_module():
    copy(logName, logSaveName)

def logAndReadFromFile(logLevel=None):

    # log    
    if logLevel is None: log(message)
    else: log(message, logLevel)

    # read what was logged
    logged = ''
    with open(logName,'r') as logFile:
        for line in logFile: pass
        logged = line
        logged = logged.split(',\t')

    return logged

# test to make sure message is being logged
# and the level is correct
def test_logDefault():
    logged = logAndReadFromFile()
    assert (logged[0],logged[-1]) == ('INFO', '"'+message+'"\n')
def test_logInfo():
    logged = logAndReadFromFile('info')
    assert (logged[0],logged[-1]) == ('INFO', '"'+message+'"\n')
def test_logDebug():
    logged = logAndReadFromFile('debug')
    assert (logged[0],logged[-1]) == ('DEBUG', '"'+message+'"\n')
def test_logWarning():
    logged = logAndReadFromFile('warning')
    assert (logged[0],logged[-1]) == ('WARNING', '"'+message+'"\n')
def test_logError():
    logged = logAndReadFromFile('error')
    assert (logged[0],logged[-1]) == ('ERROR', '"'+message+'"\n')
def test_logCritical():
    logged = logAndReadFromFile('critical')
    assert (logged[0],logged[-1]) == ('CRITICAL', '"'+message+'"\n')
def test_logInvalid(): 
    with pytest.raises(Exception):
        logAndReadFromFile('random')

# restore orignal log
def teardown_module():
    copy(logSaveName, logName)
    os.remove(logSaveName)