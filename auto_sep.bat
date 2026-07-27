@echo off
:: Change to your project directory
cd /d "C:\Users\Sepidar\Desktop\SeketalaSepidar"

:: Activate the virtual environment
call "c:\Users\Sepidar\Desktop\SeketalaSepidar\myenv\Scripts\activate.bat"

:: Run the Django server
python manage.py runserver 0.0.0.0:8600

pause
