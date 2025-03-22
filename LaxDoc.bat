@echo off
setlocal
REM Check if myenv folder exists
if not exist "myenv" (
    echo Extracting myenv.zip...
    powershell -Command "Expand-Archive -Path myenv.zip -DestinationPath ."
)
:: Check for PHP installation
where php >nul 2>nul
if %errorlevel% neq 0 (
    echo PHP is not installed. Please install PHP and ensure it is in your PATH.
    exit /b 1
)

:: Activate virtual environment
if exist myenv\Scripts\activate.bat (
    call myenv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please create it first.
    exit /b 1
)

:: Install Python dependencies if needed
pip install -r requirements.txt

:: Start PHP server
start "PHP Server" cmd /c "php -S localhost:8000"

:: Run Python GUI
python GUI/main.py
