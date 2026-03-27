@echo off
chcp 65001 >nul

echo ===============================================
echo 双模式视频生成器 (扣子/ComfyUI)
echo ===============================================

REM 检查Python环境
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误：未找到Python环境，请先安装Python并配置环境变量
    pause
    exit /b 1
)

echo 请选择视频生成器：
echo 1. 扣子视频生成器
echo 2. ComfyUI视频生成器
set /p choice="请输入选择 (1 或 2): "

if "%choice%"=="2" (
    echo 启动 ComfyUI 视频生成器...
    python comfyui_video_generator.py
) else (
    echo 启动 扣子 视频生成器...
    python kouzi_video_generator.py play1.xlsx
)

echo.
echo ===============================================
echo 任务完成！
echo ===============================================
pause