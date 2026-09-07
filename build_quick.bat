@echo off
echo ====================================================
echo Keyence PLC FTP Downloader - Quick Build Script
echo ====================================================

echo [1/2] Activating Virtual Environment...
call venv\Scripts\activate

echo [2/2] Building Executable with Nuitka...
python -m nuitka --onefile --output-filename=FTP_Control.exe --enable-plugin=tk-inter --include-package=core --include-package=ui --include-data-dir=venv\Lib\site-packages\customtkinter=customtkinter --windows-console-mode=disable --windows-icon-from-ico=app_icon.ico --include-data-files=app_icon.png=app_icon.png main.py

echo ====================================================
echo Build Complete! You can find your compiled program
echo as 'FTP_Control.exe' in the current folder.
echo ====================================================
pause
