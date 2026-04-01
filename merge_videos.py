import os
import subprocess
import sys
import re

# 检查ffmpeg是否可用
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("错误：未找到ffmpeg，请确保ffmpeg已安装并添加到系统路径中")
        return False

# 主函数
def main():
    # 检查ffmpeg
    if not check_ffmpeg():
        return
    
    # 获取项目名称
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
    else:
        project_name = input("请输入项目名称: ").strip()
    
    if not project_name:
        print("错误：项目名称不能为空")
        return
    
    # 构建输入文件夹路径
    input_folder = os.path.join("output_videos", project_name)
    
    # 检查输入文件夹是否存在
    if not os.path.exists(input_folder):
        print(f"错误：文件夹 {input_folder} 不存在")
        return
    
    # 获取所有视频文件并按名称排序
    video_files = []
    for file in os.listdir(input_folder):
        if file.endswith('.mp4'):
            video_files.append(file)
    
    if not video_files:
        print(f"错误：文件夹 {input_folder} 中没有视频文件")
        return
    
    # 按文件名排序（支持video_1.mp4, video_00008-audio.mp4等多种格式）
    def extract_number(filename):
        # 使用正则表达式提取文件名中的数字
        match = re.search(r'\d+', filename)
        if match:
            return int(match.group())
        return 0
    
    video_files.sort(key=extract_number)
    
    # 构建输出文件夹路径
    output_folder = os.path.join(input_folder, "合并")
    os.makedirs(output_folder, exist_ok=True)
    
    # 构建输出文件名
    output_file = os.path.join(output_folder, f"{project_name}_合并.mp4")
    
    # 创建临时文件列表
    temp_list_file = "temp_video_list.txt"
    with open(temp_list_file, 'w', encoding='utf-8') as f:
        for video in video_files:
            video_path = os.path.join(input_folder, video)
            f.write(f"file '{video_path}'\n")
    
    # 使用ffmpeg合并视频
    print(f"开始合并视频，共 {len(video_files)} 个视频文件...")
    try:
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_list_file,
            '-c', 'copy',
            output_file
        ]
        subprocess.run(cmd, check=True)
        print(f"视频合并成功！输出文件：{output_file}")
    except subprocess.SubprocessError as e:
        print(f"错误：合并视频失败: {e}")
    finally:
        # 删除临时文件
        if os.path.exists(temp_list_file):
            os.remove(temp_list_file)

if __name__ == "__main__":
    main()