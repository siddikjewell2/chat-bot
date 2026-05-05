@echo off
title RootTOP Assistant EXE Builder
color 0A

echo ================================================
echo     RootTOP Assistant EXE Builder
echo ================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

:: Install PyInstaller
echo Installing PyInstaller...
python -m pip install --user pyinstaller --quiet
echo.

:: Install required packages
echo Installing required packages...
python -m pip install --user llama-cpp-python==0.2.83 Pillow psutil requests --quiet
echo.

:: Clean previous builds
echo Cleaning previous builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q *.spec 2>nul
echo.

:: Build the executable (WITHOUT icon to avoid error)
echo Building EXE file...
echo This may take 3-5 minutes...

python -m PyInstaller --onefile ^
    --name "RootTOP_Assistant" ^
    --windowed ^
    --add-data "logo.jpg;." ^
    --hidden-import=llama_cpp ^
    --hidden-import=PIL ^
    --hidden-import=psutil ^
    --hidden-import=requests ^
    --collect-all=llama_cpp ^
    --noupx ^
    root_top_assistant.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create EXE
    pause
    exit /b 1
)

echo.
echo ================================================
echo     EXE CREATED SUCCESSFULLY!
echo ================================================
echo.
echo Location: dist\RootTOP_Assistant.exe
echo Size: ~50-80 MB
echo.
echo You can now:
echo 1. Copy RootTOP_Assistant.exe anywhere
echo 2. Run it without any Python installation
echo 3. Share it with others
echo.
echo NOTE: First run will still download the model (~700MB)
echo       Model will be saved in "models" folder
echo.
pause