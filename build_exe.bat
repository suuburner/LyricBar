@echo off
echo ========================================
echo    LyricBar - Quick Build Script
echo ========================================
echo.

REM Check if virtual environment exists
set "PYTHON_EXE="
if exist ".venv-1\Scripts\python.exe" (
    set "PYTHON_EXE=.venv-1\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
)

if "%PYTHON_EXE%"=="" (
    echo ERROR: Virtual environment not found!
    echo Please run this from the LyricBar directory.
    pause
    exit /b 1
)

echo Installing PyInstaller...
%PYTHON_EXE% -m pip install pyinstaller --quiet

echo.
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo Building LyricBar.exe...
echo This may take a few minutes...
echo.

%PYTHON_EXE% -m PyInstaller LyricBar.spec --noconfirm

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo    BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Your executable is at: dist\LyricBar.exe
    echo.
    echo You can now:
    echo   1. Run dist\LyricBar.exe to test it
    echo   2. Copy it anywhere you want
    echo   3. Add to Windows startup
    echo.
    
    choice /C YN /M "Would you like to run LyricBar.exe now"
    if %ERRORLEVEL% EQU 1 (
        echo.
        echo Starting LyricBar...
        start "" "dist\LyricBar.exe"
    )
) else (
    echo.
    echo ========================================
    echo    BUILD FAILED!
    echo ========================================
    echo.
    echo Check the errors above.
    pause
    exit /b 1
)

echo.
pause
