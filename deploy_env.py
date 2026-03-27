import os
import sys
import subprocess
import platform
import shutil
import ctypes
import time
import venv
from pathlib import Path

# 设置中文显示
def set_console_encoding():
    try:
        import winreg
        # 修改控制台编码为UTF-8
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                            r"Console", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "CodePage", 0, winreg.REG_DWORD, 65001)
        winreg.CloseKey(key)
    except:
        pass
    
    # 设置标准输出编码
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

# 检查是否以管理员权限运行
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 以管理员权限重启程序
def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1)

# 检查Python是否已安装
def check_python():
    print("检查Python安装状态...")
    try:
        result = subprocess.run(["python", "--version"], 
                               capture_output=True, text=True, check=True)
        python_version = result.stdout.strip()
        print(f"已安装: {python_version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("未检测到Python，请安装Python 3.8或更高版本")
        return False

# 创建项目内虚拟环境
def create_virtual_environment():
    print("创建项目内虚拟环境...")
    venv_dir = Path(".venv")
    
    if venv_dir.exists():
        print("√ 虚拟环境已存在")
        return True
    
    try:
        print("正在创建虚拟环境，请稍候...")
        venv.create(venv_dir, with_pip=True)
        print("√ 虚拟环境创建成功")
        return True
    except Exception as e:
        print(f"× 创建虚拟环境失败: {e}")
        return False

# 获取虚拟环境中的Python和pip路径
def get_venv_paths():
    if platform.system() == "Windows":
        python_exe = str(Path(".venv") / "Scripts" / "python.exe")
        pip_exe = str(Path(".venv") / "Scripts" / "pip.exe")
    else:
        python_exe = str(Path(".venv") / "bin" / "python")
        pip_exe = str(Path(".venv") / "bin" / "pip")
    
    return python_exe, pip_exe

# 安装Python依赖
def install_dependencies():
    print("安装必要的Python依赖包...")
    python_exe, pip_exe = get_venv_paths()

    if not Path(pip_exe).exists():
        print("× 无法找到虚拟环境的pip，请先创建虚拟环境")
        return False

    # 升级虚拟环境中的pip
    try:
        print("升级虚拟环境中的pip...")
        subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"],
                      capture_output=False, text=True, check=True)
        print("√ pip 升级成功")
    except subprocess.CalledProcessError as e:
        print(f"× pip 升级失败: {e}")

    dependencies = [
        "pandas",
        "openpyxl",
        "requests",
        "python-dotenv",
        "sentence-transformers"
    ]

    # 添加ComfyUI相关的额外依赖
    comfyui_dependencies = [
        "websocket-client",  # 用于与ComfyUI WebSocket通信
        "pillow"             # 用于图像处理
    ]

    all_dependencies = dependencies + comfyui_dependencies

    success = True
    for dep in all_dependencies:
        print(f"安装 {dep}...")
        try:
            subprocess.run([python_exe, "-m", "pip", "install", dep],
                          capture_output=False, text=True, check=True)
            print(f"√ {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"× {dep} 安装失败: {e}")
            # 对于ComfyUI相关依赖，即使失败也不中断整个安装过程
            if dep in dependencies:  # 核心依赖失败才影响整体成功状态
                success = False

    return success

# 检查并安装curl
def check_curl():
    print("检查curl安装状态...")
    try:
        result = subprocess.run(["curl", "--version"], 
                               capture_output=True, text=True, check=True)
        print(f"已安装: curl")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("未检测到curl，需要安装...")
        
        # 尝试通过chocolatey安装curl
        try:
            print("尝试通过chocolatey安装curl...")
            subprocess.run(["choco", "install", "curl", "-y"], 
                          capture_output=False, text=True, check=True)
            print("√ curl 安装成功")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("× 无法自动安装curl")
            print("请手动下载并安装curl: https://curl.se/windows/")
            print("安装后请将curl添加到系统PATH环境变量")
            return False

# 创建必要的目录结构
def create_directories():
    print("创建必要的目录结构...")
    required_dirs = ["images", "output_videos", "comfyui_outputs"]

    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"√ 目录 '{dir_name}' 创建成功")

# 创建或更新.env文件
def create_env_file():
    print("创建环境变量配置文件...")
    env_path = Path(".env")

    if env_path.exists():
        print(".env文件已存在，跳过创建")
        return True

    try:
        # 创建.env文件模板，包含扣子和ComfyUI配置
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# 扣子API配置\n")
            f.write("COZE_API_TOKEN=your_api_token_here\n\n")
            f.write("# ComfyUI配置\n")
            f.write("COMFYUI_API_BASE=http://localhost:8188\n")
            f.write("COMFYUI_WORKFLOW_JSON=workflow.json\n")

        print(f"√ .env文件创建成功，请编辑 {env_path} 填入您的API令牌和ComfyUI配置")
        return True
    except Exception as e:
        print(f"× 创建.env文件失败: {e}")
        return False

# 复制示例文件
def copy_example_files():
    print("复制示例文件...")

    # 如果没有play1.xlsx但有示例配置文件.xlsx，则复制
    if not Path("play1.xlsx").exists() and Path("示例配置文件.xlsx").exists():
        try:
            shutil.copy("示例配置文件.xlsx", "play1.xlsx")
            print("√ 已复制示例配置文件到 play1.xlsx")
        except Exception as e:
            print(f"× 复制示例配置文件失败: {e}")

    # 确保workflow.json文件存在
    workflow_file = Path("workflow.json")
    if not workflow_file.exists():
        print("⚠️  workflow.json 文件不存在，ComfyUI视频生成功能将不可用")
        print("   请确保workflow.json文件在项目根目录中")
    else:
        print("√ workflow.json 文件已存在")

# 打包相关功能已移除

# 主部署函数
def deploy_environment():
    print("====================================")
    print("扣子视频生成器环境部署工具")
    print("====================================")
    
    # 检查操作系统
    if platform.system() != "Windows":
        print("错误: 此部署工具仅支持Windows操作系统")
        input("按回车键退出...")
        return False
    
    # 检查Python
    if not check_python():
        print("请先安装Python 3.8或更高版本，然后重新运行此程序")
        print("Python下载地址: https://www.python.org/downloads/")
        input("安装完成后按回车键重试...")
        return False
    
    # 创建项目内虚拟环境
    if not create_virtual_environment():
        print("创建虚拟环境失败，无法继续")
        input("按回车键退出...")
        return False
    
    # 安装依赖到虚拟环境
    if not install_dependencies():
        print("部分依赖安装失败，请检查网络连接后重试")
        retry = input("是否重试安装依赖? (y/n): ")
        if retry.lower() == 'y':
            install_dependencies()
    
    # 检查curl
    check_curl()
    
    # 创建目录
    create_directories()
    
    # 创建环境变量文件
    create_env_file()
    
    # 复制示例文件
    copy_example_files()
    
    # 创建运行脚本
    create_run_script()
    # 更新生成.bat文件
    update_generate_bat()
    
    print("\n====================================")
    print("部署完成!")
    print("====================================")
    print("1. 请确保已在.env文件中配置了您的API令牌")
    print("2. 您可以运行 'run_project.bat' 启动项目")
    print("3. 或在命令行中使用虚拟环境: .venv\\Scripts\\python kouzi_video_generator.py [Excel文件]")
    print("====================================")
    input("按回车键退出...")
    return True

# 获取程序的实际运行目录
def get_actual_path():
    # 处理PyInstaller打包后的情况
    if hasattr(sys, '_MEIPASS'):
        # 当程序被打包为EXE时，返回EXE所在目录
        return os.path.dirname(sys.executable)
    else:
        # 当直接运行Python脚本时，返回脚本所在目录
        return os.path.dirname(os.path.abspath(__file__))

# 创建运行脚本
def create_run_script():
    print("创建项目运行脚本...")

    # 创建Windows批处理文件支持两个生成器
    bat_content = "@echo off\n"
    bat_content += "REM 视频生成器运行脚本 - 支持扣子和ComfyUI两种模式\n"
    bat_content += "REM 此脚本使用项目内虚拟环境运行视频生成器\n\n"
    bat_content += "cls\n"
    bat_content += "echo ================================\n"
    bat_content += "echo 视频生成器 (扣子/ComfyUI)\n"
    bat_content += "===============================\n\n"

    # 检查虚拟环境
    bat_content += "REM 检查虚拟环境是否存在\n"
    bat_content += "if not exist \".venv\\Scripts\\python.exe\" (\n"
    bat_content += "    echo 错误：虚拟环境不存在，请先运行部署环境.exe\n"
    bat_content += "    pause\n"
    bat_content += "    exit /b 1\n"
    bat_content += ")\n\n"

    # 选择生成器模式
    bat_content += "echo 请选择视频生成器模式：\n"
    bat_content += "echo 1. 扣子视频生成器\n"
    bat_content += "echo 2. ComfyUI视频生成器\n"
    bat_content += "set /p mode_choice=\"请输入选择 (1 或 2, 默认为1): \"\n"
    bat_content += "if \"!mode_choice!\"==\"\" set mode_choice=1\n\n"
    bat_content += "if \"!mode_choice!\"==\"2\" (\n"
    bat_content += "    set \"generator_script=comfyui_video_generator.py\"\n"
    bat_content += "    echo 使用 ComfyUI 视频生成器\n"
    bat_content += "    echo 注意：请确保 ComfyUI 服务正在运行 (默认地址: http://localhost:8188)\n"
    bat_content += ") else (\n"
    bat_content += "    set \"generator_script=kouzi_video_generator.py\"\n"
    bat_content += "    echo 使用 扣子 视频生成器\n"
    bat_content += ")\n\n"

    # Excel文件选择
    bat_content += "REM 检查Excel文件参数\n"
    bat_content += "if \"%2\"==\"\" (\n"  # Changed from %1 since %1 is now mode_choice
    bat_content += "    echo 检测到以下Excel文件:\n"
    bat_content += "    setlocal enabledelayedexpansion\n"
    bat_content += "    set count=0\n\n"
    bat_content += "    for %%f in (*.xlsx) do (\n"
    bat_content += "        set /a count+=1\n"
    bat_content += "        set \"file[!count!]=%%f\"\n"
    bat_content += "        echo !count!. %%f\n"
    bat_content += "    )\n\n"
    bat_content += "    if !count! equ 0 (\n"
    bat_content += "        echo 未检测到Excel文件，请先创建配置文件\n"
    bat_content += "        pause\n"
    bat_content += "        exit /b 1\n"
    bat_content += "    )\n\n"
    bat_content += "    set /p choice=\"请选择要处理的文件 (1-!count!, 默认为1): \"\n"
    bat_content += "    if \"!choice!\"==\"\" set choice=1\n\n"
    bat_content += "    for %%i in (1 2 3 4 5 6 7 8 9 10) do (\n"
    bat_content += "        if !choice! equ %%i (\n"
    bat_content += "            set \"excel_file=!file[%%i]!\"\n"
    bat_content += "            goto :found\n"
    bat_content += "        )\n"
    bat_content += "    )\n"
    bat_content += "    set \"excel_file=!file[1]!\"\n"
    bat_content += "    :found\n"
    bat_content += "    endlocal & set \"excel_file=%excel_file%\"\n"
    bat_content += ") else (\n"
    bat_content += "    set \"excel_file=%2\"\n"  # Changed to %2 since %1 is mode_choice
    bat_content += ")\n\n"

    bat_content += "echo.\n"
    bat_content += "echo 开始处理文件: %excel_file%\n"
    bat_content += "echo.\n\n"

    # 运行相应的生成器
    bat_content += "REM 使用虚拟环境中的Python运行选定的视频生成器\n"
    bat_content += ".venv\\Scripts\\python.exe %generator_script% \"%excel_file%\"\n\n"

    bat_content += "REM 保持窗口打开\n"
    bat_content += "pause"

    try:
        with open("run_project.bat", "w", encoding="utf-8") as f:
            f.write(bat_content)
        print("√ 运行脚本 run_project.bat 创建成功")
    except Exception as e:
        print(f"× 创建运行脚本失败: {e}")

    # Also update the generate batch file to support both generators
    update_generate_bat()


def update_generate_bat():
    print("更新生成.bat文件...")

    # 创建支持双模式的批处理文件
    generate_bat_content = "@echo off\n"
    generate_bat_content += "chcp 65001 >nul\n\n"
    generate_bat_content += "echo ===============================================\n"
    generate_bat_content += "echo 双模式视频生成器 (扣子/ComfyUI)\n"
    generate_bat_content += "echo ===============================================\n\n"

    # 检查Python
    generate_bat_content += "REM 检查Python环境\n"
    generate_bat_content += "python --version >nul 2>&1\n"
    generate_bat_content += "if %ERRORLEVEL% neq 0 (\n"
    generate_bat_content += "    echo 错误：未找到Python环境，请先安装Python并配置环境变量\n"
    generate_bat_content += "    pause\n"
    generate_bat_content += "    exit /b 1\n"
    generate_bat_content += ")\n\n"

    # 询问模式选择
    generate_bat_content += "echo 请选择视频生成器：\n"
    generate_bat_content += "echo 1. 扣子视频生成器\n"
    generate_bat_content += "echo 2. ComfyUI视频生成器\n"
    generate_bat_content += "set /p choice=\"请输入选择 (1 或 2): \"\n\n"

    generate_bat_content += "if \"%choice%\"==\"2\" (\n"
    generate_bat_content += "    echo 启动 ComfyUI 视频生成器...\n"
    generate_bat_content += "    python comfyui_video_generator.py\n"
    generate_bat_content += ") else (\n"
    generate_bat_content += "    echo 启动 扣子 视频生成器...\n"
    generate_bat_content += "    python kouzi_video_generator.py play1.xlsx\n"
    generate_bat_content += ")\n\n"

    generate_bat_content += "echo.\n"
    generate_bat_content += "echo ===============================================\n"
    generate_bat_content += "echo 任务完成！\n"
    generate_bat_content += "echo ===============================================\n"
    generate_bat_content += "pause"

    try:
        with open("生成.bat", "w", encoding="utf-8") as f:
            f.write(generate_bat_content)
        print("√ 生成.bat文件更新成功")
    except Exception as e:
        print(f"× 更新生成.bat文件失败: {e}")

    # 也要更新生成_ComfyUI.bat
    comfyui_bat_content = "@echo off\n"
    comfyui_bat_content += "chcp 65001 >nul\n\n"
    comfyui_bat_content += "echo ===============================================\n"
    comfyui_bat_content += "echo ComfyUI视频生成器\n"
    comfyui_bat_content += "echo ===============================================\n"
    comfyui_bat_content += "echo 正在启动视频生成流程...\n"
    comfyui_bat_content += "echo.\n\n"

    comfyui_bat_content += "REM 检查Python是否安装\n"
    comfyui_bat_content += "python --version >nul 2>&1\n"
    comfyui_bat_content += "if %ERRORLEVEL% neq 0 (\n"
    comfyui_bat_content += "    echo 错误：未找到Python环境，请先安装Python并配置环境变量\n"
    comfyui_bat_content += "    pause\n"
    comfyui_bat_content += "    exit /b 1\n"
    comfyui_bat_content += ")\n\n"

    comfyui_bat_content += "echo 检查并安装依赖...\n"
    comfyui_bat_content += "pip install -r requirements.txt\n"
    comfyui_bat_content += "if %ERRORLEVEL% neq 0 (\n"
    comfyui_bat_content += "    echo 警告：依赖安装可能出现问题，但仍将继续\n"
    comfyui_bat_content += ")\n\n"

    comfyui_bat_content += "echo 依赖检查完成\n\n"

    comfyui_bat_content += "REM 检查.env文件是否存在\n"
    comfyui_bat_content += "if not exist .env (\n"
    comfyui_bat_content += "    echo 警告：未找到.env文件，将使用默认配置\n"
    comfyui_bat_content += "    echo 建议：复制.env.example为.env并配置ComfyUI API地址\n"
    comfyui_bat_content += ")\n\n"

    comfyui_bat_content += "echo.\n"
    comfyui_bat_content += "echo ===============================================\n"
    comfyui_bat_content += "echo 请输入Excel配置文件路径（默认：示例配置文件.xlsx）\n"
    comfyui_bat_content += "echo ===============================================\n"
    comfyui_bat_content += "set /p excel_path=\"配置文件路径: \"\n\n"

    comfyui_bat_content += "REM 如果用户未输入，使用默认值\n"
    comfyui_bat_content += "if \"%excel_path%\" == \"\" set excel_path=\"示例配置文件.xlsx\"\n\n"

    comfyui_bat_content += "REM 运行视频生成脚本\n"
    comfyui_bat_content += "python comfyui_video_generator.py %excel_path%\n\n"

    comfyui_bat_content += "if %ERRORLEVEL% neq 0 (\n"
    comfyui_bat_content += "    echo 错误：视频生成过程中出现异常\n"
    comfyui_bat_content += "    pause\n"
    comfyui_bat_content += "    exit /b 1\n"
    comfyui_bat_content += ")\n\n"

    comfyui_bat_content += "echo.\n"
    comfyui_bat_content += "echo ===============================================\n"
    comfyui_bat_content += "echo 视频生成完成！\n"
    comfyui_bat_content += "echo 输出结果保存在 output.xlsx 文件中\n"
    comfyui_bat_content += "echo ===============================================\n"
    comfyui_bat_content += "pause"

    try:
        with open("生成_ComfyUI.bat", "w", encoding="utf-8") as f:
            f.write(comfyui_bat_content)
        print("√ 生成_ComfyUI.bat文件更新成功")
    except Exception as e:
        print(f"× 更新生成_ComfyUI.bat文件失败: {e}")

    # 检查管理员权限
    if not is_admin():
        print("提示: 以管理员权限运行可以获得更好的体验")
        choice = input("是否以管理员权限重启程序? (y/n): ")
        if choice.lower() == 'y':
            run_as_admin()
            sys.exit()
    
    # 开始部署
    deploy_environment()