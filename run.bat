@echo off
cd /d "%~dp0"
echo ========================================
echo  منصة تحليل البورصة المصرية
echo  جاري تشغيل التطبيق...
echo  سيتم فتح المتصفح تلقائيا
echo  للتوقف: اضغط Ctrl + C
echo ========================================
set PYTHONIOENCODING=utf-8
start "" http://localhost:8501
python -m streamlit run app.py
pause
