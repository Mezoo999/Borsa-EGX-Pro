@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   تسجيل مهمة مجدولة: التقرير الصباحي 9:30 (الأحد - الخميس)
echo ============================================================
set "PYEXE="
for /f "delims=" %%i in ('py -3.12 -c "import sys;print(sys.executable)" 2^>nul') do set "PYEXE=%%i"
if "%PYEXE%"=="" set "PYEXE=python"
echo ملف بايثون: %PYEXE%
schtasks /Create /TN "EGX Morning Report" ^
  /TR ""%PYEXE%" "%~dp0daily_report.py"" ^
  /SC WEEKLY /D SUN,MON,TUE,WED,THU /ST 09:30 /F
if %errorlevel%==0 (
    echo.
    echo ✅ تم تسجيل المهمة: "EGX Morning Report" ^(9:30 صباحاً، الأحد-الخميس^)
) else (
    echo.
    echo ⚠️ تعذّر التسجيل — شغّل هذا الملف كمسؤول ^(Run as administrator^)^
)
pause
