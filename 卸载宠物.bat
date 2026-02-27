@echo off
chcp 65001 >nul
echo ====================================
echo Claude 宠物伴侣 - 卸载程序
echo ====================================
echo.

REM 检查是否在正确的目录
if not exist "install.py" (
    echo 请在 claude-pet-companion 目录中运行此脚本
    pause
    exit /b 1
)

echo 请选择卸载选项:
echo.
echo 1. 仅卸载插件（保留存档数据）
echo 2. 完全卸载（删除所有数据）
echo 3. 取消
echo.

set /p choice="请输入选项 (1-3): "

if "%choice%"=="1" (
    echo.
    echo 正在卸载插件...
    python install.py uninstall
) else if "%choice%"=="2" (
    echo.
    echo 警告: 此操作将删除所有存档数据！
    set /p confirm="确认完全卸载? (yes/no): "
    if /i "%confirm%"=="yes" (
        echo.
        echo 正在完全卸载...
        python install.py uninstall --all
    ) else (
        echo 已取消卸载。
    )
) else (
    echo 已取消卸载。
)

echo.
pause
