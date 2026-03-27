@echo off
chcp 65001 >nul

echo ===============================================
echo ComfyUI视频生成器
echo ===============================================
echo 正在启动视频生成流程...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误：未找到Python环境，请先安装Python并配置环境变量
    pause
    exit /b 1
)

echo 检查并安装依赖...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo 警告：依赖安装可能出现问题，但仍将继续
)

echo 依赖检查完成

REM 检查.env文件是否存在
if not exist .env (
    echo 警告：未找到.env文件，将使用默认配置
    echo 建议：复制.env.example为.env并配置ComfyUI API地址
)

echo.
echo ===============================================
echo 请输入Excel配置文件路径（默认：示例配置文件.xlsx）
echo ===============================================
set /p excel_path="配置文件路径: "

REM 如果用户未输入，使用默认值
if "%excel_path%" == "" set excel_path="示例配置文件.xlsx"

REM 运行视频生成脚本
python comfyui_video_generator.py %excel_path%

if %ERRORLEVEL% neq 0 (
    echo 错误：视频生成过程中出现异常
    pause
    exit /b 1
)

echo.
echo ===============================================
echo 视频生成完成！
echo 输出结果保存在 output.xlsx 文件中
echo ===============================================
pause