@echo off
setlocal
cd /d "%~dp0"

echo ==================================================
echo  Cybersecurity Learning Hub
echo ==================================================
echo.

echo [1/3] Checking the project environment...

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Project Python environment was not found.
    goto failed
)

".venv\Scripts\python.exe" -c "import fastapi, uvicorn, pwdlib, itsdangerous, mysql.connector"

if errorlevel 1 (
    echo [ERROR] A required Python package is missing.
    goto failed
)

echo [OK] Python environment is ready.
echo.

echo [2/3] Checking the database...

".venv\Scripts\python.exe" database.py

if errorlevel 1 (
    echo [ERROR] Database initialisation failed.
    goto failed
)

echo [OK] Database is ready.
echo.

echo [3/3] Starting the website...
echo.
echo Home:     http://127.0.0.1:8002/
echo Register: http://127.0.0.1:8002/signup
echo Login:    http://127.0.0.1:8002/login
echo.
echo Keep this window open.
echo Requests and results will appear below.
echo Press Ctrl+C to stop the website.
echo.

".venv\Scripts\python.exe" -u -m uvicorn main:app --host 127.0.0.1 --port 8002 --log-level info --access-log

if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo Startup failed. Review the error above.
pause
exit /b 1