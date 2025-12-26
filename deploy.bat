@echo off
echo Starting deployment...

REM Add all changes
git add .

REM Check for commit message argument
if "%~1"=="" (
    set /p msg="Enter commit message (Press Enter for default): "
) else (
    set msg=%~1
)

REM Set default message if empty
if "%msg%"=="" set msg="Auto deploy update"

REM Commit changes
git commit -m "%msg%"

REM Push to remote
echo Pushing to GitHub...
git push origin main

echo.
echo Deployment triggered!
echo 1. Changes pushed to GitHub.
echo 2. Vercel will automatically detect the push and start building.
echo 3. Check deployment status at: https://vercel.com/dashboard
echo.
pause
