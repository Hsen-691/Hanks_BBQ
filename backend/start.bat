
@echo off
REM Start the Hank's BBQ backend (serves the API and the website on APP_PORT).
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo Could not find the virtual environment at .venv
    echo Create it first: py -3.11 -m venv .venv ^&^& .venv\Scripts\python -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

REM If uvicorn exits with an error (e.g. port 8000 already in use), keep the
REM window open so the message is readable instead of flashing closed.
if errorlevel 1 (
    echo.
    echo The server stopped with an error ^(see the message above^).
    echo If it says the address is already in use, port 8000 is taken by another
    echo instance - close it, or change the port, then run this again.
    echo.
    pause
)
