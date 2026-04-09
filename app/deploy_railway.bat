@echo off
echo =========================
echo 🚀 Deploy a Railway
echo =========================

git status

echo.
set /p msg=Escribe el mensaje del commit: 

git add .
git commit -m "%msg%"
git push

echo.
echo ✅ Codigo subido a GitHub
echo 🚀 Railway desplegara automaticamente
pause