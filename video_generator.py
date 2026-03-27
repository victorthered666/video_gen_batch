import pandas as pd
import requests
import os
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class SkyreelsVideoGenerator:
    def __init__(self):
        self.skyreels_api_url = os.getenv("SKYREELS_API_URL", "http://localhost:8000/generate")
        self.image_dir = "images"  # 图片文件夹
        os.makedirs(self.image_dir, exist_ok=True)
        self.output_dir = "output_videos"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_excel_config(self, excel_path):
        """加载Excel配置文件"""
        try:
            df = pd.read_excel(excel_path)
            print(f"成功加载Excel文件，共读取到 {len(df)} 条记录")
            return df
        except Exception as e:
            print(f"读取Excel文件失败: {str(e)}")
            return None
    
    def validate_config(self, df):
        """验证配置文件的必要列是否存在"""
        required_columns = ['序号', '首帧', '尾帧', '画面镜头描述', '是否生效']
        for col in required_columns:
            if col not in df.columns:
                print(f"错误：配置文件缺少必要列 '{col}'")
                return False
        return True
    
    def generate_video(self, config_row):
        """使用skyreels模型生成视频"""
        # 检查是否需要生成（是否生效为True）
        if not config_row['是否生效']:
            print(f"序号 {config_row['序号']} 的记录未生效，跳过生成")
            return None
        
        try:
            # 准备请求数据
            payload = {
                "start_image": config_row['首帧'],  # 首帧现在是图片地址
                "end_image": config_row['尾帧'],    # 尾帧现在是图片地址
                "description": config_row['画面镜头描述']
            }
            
            print(f"正在生成序号 {config_row['序号']} 的视频...")
            print(f"描述: {config_row['画面镜头描述']}")
            print(f"图片范围: {config_row['首帧']} - {config_row['尾帧']}")
            
            # 确保图片路径是绝对路径或正确的相对路径
            if not os.path.isabs(config_row['首帧']):
                payload['start_image'] = os.path.join(self.image_dir, config_row['首帧'])
            if not os.path.isabs(config_row['尾帧']):
                payload['end_image'] = os.path.join(self.image_dir, config_row['尾帧'])
            
            # 验证图片文件是否存在
            if not os.path.exists(payload['start_image']):
                print(f"错误：首帧图片 '{payload['start_image']}' 不存在")
                return None
            if not os.path.exists(payload['end_image']):
                print(f"错误：尾帧图片 '{payload['end_image']}' 不存在")
                return None
            
            # 调用skyreels API生成视频
            # 注意：这里假设API的调用方式，实际使用时需要根据真实API进行调整
            # 根据API要求，可能需要调整为上传图片文件而非仅提供路径
            response = requests.post(self.skyreels_api_url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                video_path = os.path.join(self.output_dir, f"video_{config_row['序号']}.mp4")
                
                # 保存视频文件（这里只是示例，实际需要根据API返回调整）
                if 'video_url' in result:
                    # 如果API返回视频URL，下载视频
                    video_response = requests.get(result['video_url'])
                    with open(video_path, 'wb') as f:
                        f.write(video_response.content)
                    print(f"视频已保存: {video_path}")
                    return video_path
                elif 'video_data' in result:
                    # 如果API直接返回视频数据
                    import base64
                    with open(video_path, 'wb') as f:
                        f.write(base64.b64decode(result['video_data']))
                    print(f"视频已保存: {video_path}")
                    return video_path
                else:
                    print(f"API返回格式不支持: {result}")
                    return None
            else:
                print(f"API调用失败，状态码: {response.status_code}, 响应: {response.text}")
                return None
                
        except Exception as e:
            print(f"生成视频时出错: {str(e)}")
            return None
    
    def process_all(self, excel_path):
        """处理Excel中的所有记录"""
        # 加载配置
        df = self.load_excel_config(excel_path)
        if df is None:
            return
        
        # 验证配置
        if not self.validate_config(df):
            return
        
        # 处理每条记录
        success_count = 0
        total_count = len(df)
        
        for index, row in df.iterrows():
            print(f"\n----- 处理第 {index + 1}/{total_count} 条记录 -----")
            video_path = self.generate_video(row)
            if video_path:
                success_count += 1
            
            # 避免API请求过于频繁
            if index < total_count - 1:
                print("等待2秒后处理下一条记录...")
                time.sleep(2)
        
        print(f"\n----- 处理完成 -----")
        print(f"总记录数: {total_count}")
        print(f"成功生成: {success_count}")
        print(f"失败数量: {total_count - success_count}")
        print(f"生成的视频保存在: {os.path.abspath(self.output_dir)}")

if __name__ == "__main__":
    print("=== Skyreels视频生成器 ===")
    print("本程序将读取Excel配置文件，并使用skyreels模型生成视频")
    
    # 提示用户输入Excel文件路径
    excel_path = input("请输入Excel配置文件路径: ").strip()
    
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        print(f"错误：文件 '{excel_path}' 不存在")
        exit(1)
    
    # 创建生成器实例并处理
    generator = SkyreelsVideoGenerator()
    generator.process_all(excel_path)