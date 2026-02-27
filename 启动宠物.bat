@echo off
chcp 65001 >nul 2>&1
title Claude Code Pet HD v2.0
echo ================================
echo   Claude Code Pet HD v2.0
echo ================================
echo.
echo Starting your Claude companion...
echo.
python "%~dp0claude_pet_companion\claude_pet_hd.py"
if errorlevel 1 (
    echo.
    echo Error: Failed to start pet.
    echo Make sure Python 3.8+ is installed.
    pause
)
