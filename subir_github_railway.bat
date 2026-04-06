@echo off
setlocal

cd /d "%~dp0"

echo ================================
echo   BOT ACROJAS V2 - PUSH + DEPLOY
echo ================================
echo.

git status

echo.
set /p msg=Escribe el mensaje del commit: 
if "%msg%"=="" set msg=update bot_acrojas_v2

echo.
git add .

git diff --cached --quiet
if %errorlevel%==0 (
    echo.
    echo ⚠️ No hay cambios para commitear.
    pause
    exit /b 0
)

git commit -m "%msg%"
if errorlevel 1 (
    echo.
    echo ❌ Error en commit.
    pause
    exit /b 1
)

git push
if errorlevel 1 (
    echo.
    echo ❌ Error al hacer push.
    pause
    exit /b 1
)

echo.
echo ================================
echo   🚀 CAMBIOS SUBIDOS A GITHUB
echo   Railway desplegara automaticamente
echo ================================
echo.
pause