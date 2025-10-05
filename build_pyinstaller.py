#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт компиляции AutoGun с PyInstaller
"""

import subprocess
import sys
import os
import shutil

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 13:
        print("=" * 50)
        print("ВНИМАНИЕ: Python 3.13 не поддерживается!")
        print("=" * 50)
        print("\nИспользуйте Python 3.12:")
        print("1. Активируйте venv: venv312\\Scripts\\activate")
        print("2. Запустите: python build_pyinstaller.py")
        input("\nНажмите Enter...")
        sys.exit(1)

def install_pyinstaller():
    """Установка PyInstaller"""
    print("\n" + "=" * 50)
    print("  Установка PyInstaller...")
    print("=" * 50)
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "pyinstaller"
    ])

def clean_build_dirs():
    """Очистка предыдущих сборок"""
    print("\n" + "=" * 50)
    print("  Очистка предыдущих сборок...")
    print("=" * 50)
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dirname in dirs_to_clean:
        if os.path.exists(dirname):
            print(f"  Удаление: {dirname}/")
            shutil.rmtree(dirname, ignore_errors=True)

def compile_with_pyinstaller():
    """Компиляция с PyInstaller"""
    print("\n" + "=" * 50)
    print("  КОМПИЛЯЦИЯ НАЧАЛАСЬ")
    print("  Это займёт 5-15 минут!")
    print("  Не закрывайте окно!")
    print("=" * 50 + "\n")
    
    # Используем готовый spec-файл
    if os.path.exists("AutoGun.spec"):
        print("  Используется AutoGun.spec\n")
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",           # Очистка перед сборкой
            "--noconfirm",       # Не спрашивать подтверждения
            "AutoGun.spec"
        ]
    else:
        # Fallback: сборка без spec-файла
        print("  ПРЕДУПРЕЖДЕНИЕ: AutoGun.spec не найден!")
        print("  Используется базовая конфигурация\n")
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            "--name=AutoGun",
            "--hidden-import=pymem",
            "--hidden-import=keyboard",
            "--hidden-import=mouse",
            "--hidden-import=loguru",
            "--hidden-import=yaml",
            "--add-data=config;config",
            "--add-data=data;data",
            "main.py"
        ]
    
    result = subprocess.run(cmd)
    return result.returncode

def copy_exe_to_root():
    """Копирование exe в корень проекта"""
    dist_exe = os.path.join("dist", "AutoGun.exe")
    root_exe = "AutoGun.exe"
    
    if os.path.exists(dist_exe):
        print("\n" + "=" * 50)
        print("  Копирование AutoGun.exe в корень...")
        print("=" * 50)
        
        # Удаляем старый exe если есть
        if os.path.exists(root_exe):
            os.remove(root_exe)
        
        # Копируем новый
        shutil.copy2(dist_exe, root_exe)
        return True
    return False

def main():
    """Главная функция"""
    print("=" * 50)
    print("  Компиляция AutoGun с PyInstaller")
    print("=" * 50)
    
    # Проверка версии
    check_python_version()
    
    # Установка PyInstaller
    install_pyinstaller()
    
    # Очистка
    clean_build_dirs()
    
    # Компиляция
    exit_code = compile_with_pyinstaller()
    
    # Результат
    print("\n" + "=" * 50)
    if exit_code == 0:
        if copy_exe_to_root():
            print("  ✓ УСПЕШНО!")
            print("  Файл: AutoGun.exe")
            if os.path.exists("AutoGun.exe"):
                size_mb = os.path.getsize("AutoGun.exe") / (1024 * 1024)
                print(f"  Размер: {size_mb:.1f} МБ")
            print()
            print("  ВАЖНО:")
            print("  - Запускайте AutoGun.exe из этой папки")
            print("  - Рядом должны быть папки config/ и data/")
        else:
            print("  ✗ Файл не найден в dist/")
    else:
        print("  ✗ ОШИБКА КОМПИЛЯЦИИ!")
        print("\n  Возможные проблемы:")
        print("  1. Не все зависимости установлены")
        print("  2. Используется Python 3.13 (нужен 3.12)")
        print("  3. Проблема с PyQt6")
        print("\n  Решение:")
        print("  1. Активируйте venv312: venv312\\Scripts\\activate")
        print("  2. Установите зависимости: pip install -r requirements.txt")
        print("  3. Запустите снова: python build_pyinstaller.py")
    print("=" * 50)
    
    input("\nНажмите Enter...")

if __name__ == "__main__":
    main()
