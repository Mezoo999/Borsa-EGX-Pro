@echo off
chcp 65001 >nul
echo إزالة مهمة التقرير الصباحي...
schtasks /Delete /TN "EGX Morning Report" /F
pause
