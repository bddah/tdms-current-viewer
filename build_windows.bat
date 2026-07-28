@echo off
pip install -r requirements_desktop.txt
pyinstaller tdms_desktop.spec
echo.
echo Build complete. Executable is in dist\TdmsViewer\
pause
