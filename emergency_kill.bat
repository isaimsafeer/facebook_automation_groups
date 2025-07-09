@echo off
echo Emergency kill script activated!
echo Killing all Python processes...
taskkill /F /IM python.exe

echo Removing any lock files...
if exist TERMINATING.lock del TERMINATING.lock
if exist emergency_kill.bat del emergency_kill.bat

echo Done.
pause 