@echo off
echo =========================
echo 🚀 Deploy a Railway
echo =========================

git add .
git commit -m "deploy update"
git push

echo.
echo ✅ Codigo subido a GitHub
echo Railway se encargara del deploy automaticamente
pause