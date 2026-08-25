@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 패키지 설치 중...
python -m pip install -r requirements.txt -q
echo 대시보드를 켭니다.
python gui_app.py
pause
