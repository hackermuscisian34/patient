@echo off
cd /d "c:\Users\alber\OneDrive\Scans\patient\CascadeProjects\windsurf-project"
echo Running Patient Tracker Setup Test...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the test
python test_setup.py

pause
