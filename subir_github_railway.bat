@echo off
setlocal

cd /d "%~dp0"

echo ================================
echo   BOT ACROJAS V2 - GITHUB PUSH
echo ================================
echo.

git status

echo.
set /p msg=Escribe el mensaje del commit: 
if "%msg%"=="" set msg=update bot_acrojas_v2

echo.
git add .
git commit -m "%msg%"
git push

echo.
echo ================================
echo   CAMBIOS SUBIDOS A GITHUB
echo ================================
echo.
pause
