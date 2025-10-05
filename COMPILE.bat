@echo off
chcp 65001 >nul
title Компиляция AutoGun

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║          КОМПИЛЯЦИЯ AUTOGUN                        ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM Проверка активации venv
python --version 2>nul | find "3.12" >nul
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python 3.12 не найден!
    echo.
    echo Сначала активируйте виртуальное окружение:
    echo   venv312\Scripts\activate
    echo.
    echo Затем запустите снова:
    echo   COMPILE.bat
    echo.
    pause
    exit /b 1
)

echo [OK] Python 3.12 найден
echo.

REM Установка зависимостей
echo Проверка зависимостей...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] PyInstaller не установлен, устанавливаю...
    pip install pyinstaller
)

REM Запуск компиляции
echo.
echo ────────────────────────────────────────────────────
echo   ЗАПУСК КОМПИЛЯЦИИ
echo ────────────────────────────────────────────────────
echo.

python build_pyinstaller.py

exit /b %errorlevel%
