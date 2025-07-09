
@echo off
echo Forcibly terminating Python process 13012...
taskkill /F /PID 13012
echo Process should be terminated.
del "%~f0"
