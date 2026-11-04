@echo off
REM Back up the Hank's BBQ database to a compressed dump, then delete dumps older
REM than 14 days. Schedule this daily (see README).
REM
REM SECURITY:
REM  * No password is stored in this file. pg_dump reads it from PostgreSQL's own
REM    password file:  %APPDATA%\postgresql\pgpass.conf   with ONE line:
REM        localhost:5432:hanks_bbq:hanks_user:YOUR-DB-PASSWORD
REM  * Dumps go OUTSIDE the project folder (default C:\hanks-backups) so they can
REM    never be uploaded or served with the website. To use another folder, set the
REM    HANKS_BACKUP_DIR environment variable.
setlocal
set PGBIN=C:\Program Files\PostgreSQL\17\bin
if "%HANKS_BACKUP_DIR%"=="" set HANKS_BACKUP_DIR=C:\hanks-backups
set BK=%HANKS_BACKUP_DIR%
if not exist "%BK%" mkdir "%BK%"

REM Timestamp: YYYYMMDD_HHMMSS (locale-independent, via PowerShell).
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set STAMP=%%I
set FILE=%BK%\hanks_bbq_%STAMP%.dump

"%PGBIN%\pg_dump.exe" -U hanks_user -h localhost -d hanks_bbq -w -Fc -f "%FILE%"
if errorlevel 1 (
  echo Backup FAILED. Check that %APPDATA%\postgresql\pgpass.conf exists and is correct.
  exit /b 1
)
echo Backup written to %FILE%

REM Keep the last 14 days of dumps.
powershell -NoProfile -Command "Get-ChildItem '%BK%\*.dump' | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } | Remove-Item -Force"
endlocal
