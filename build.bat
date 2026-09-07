@echo off
echo ====================================================
echo Keyence PLC FTP Downloader - Build Script (Nuitka)
echo ====================================================

echo [1/3] Activating Virtual Environment...
call venv\Scripts\activate

echo [2/3] Installing Required Libraries (Requirements + Nuitka)...
pip install -r requirements.txt
pip install nuitka

echo [3/3] Building Executable with Nuitka...
:: --standalone : Create a standalone folder
:: --onefile : Create a single .exe file (optional, might take longer to extract on startup)
:: --enable-plugin=tk-inter : Required for Tkinter/CustomTkinter to bundle Tcl/Tk binaries
:: --include-data-dir : Bundle customtkinter assets
:: --windows-console-mode=disable : Hide the black CMD console when running the GUI

python -m nuitka --onefile --output-filename=FTP_Control.exe --enable-plugin=tk-inter --include-package=core --include-package=ui --include-data-dir=venv\Lib\site-packages\customtkinter=customtkinter --windows-console-mode=disable --windows-icon-from-ico=app_icon.ico --include-data-files=app_icon.png=app_icon.png main.py

echo ====================================================
echo Build Complete! You can find your compiled program
echo as 'FTP_Control.exe' in the current folder.
echo ====================================================
pause
