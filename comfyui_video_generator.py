import os
import sys
import time
import json
import pandas as pd
import subprocess
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ComfyUI配置
COMFYUI_API_BASE = os.getenv("COMFYUI_API_BASE", "http://localhost:8188")
COMFYUI_WORKFLOW_JSON = os.getenv("COMFYUI_WORKFLOW_JSON", "wan2.2_FLFrames_Audio_Subtitle.json")

class ComfyUIVideoGenerator:
    def __init__(self, excel_filename):
        """初始化视频生成器
        
        Args:
            excel_filename: 表格文件名，用于创建输出文件夹
        """
        self.api_base = COMFYUI_API_BASE
        self.workflow_file = COMFYUI_WORKFLOW_JSON
        self.image_dir = "images"  # 图片文件夹
        
        # 根据表格文件名创建输出文件夹
        excel_basename = os.path.splitext(os.path.basename(excel_filename))[0]
        self.output_dir = os.path.join("output_videos", excel_basename)  # 视频输出文件夹
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_excel_config(self, excel_path):
        """加载Excel配置文件"""
        try:
            df = pd.read_excel(excel_path)
            print(f"成功加载Excel文件，共读取到 {len(df)} 条记录")
            return df
        except Exception as e:
            print(f"读取Excel失败: {str(e)}")
            return None
    
    def validate_config(self, df):
        """验证配置文件的必要列是否存在"""
        required_columns = ['序号', '首帧', '尾帧', '画面镜头描述', '是否生效']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"错误：缺少必要列: {', '.join(missing_columns)}")
            return False
        
        return True
    
    def load_workflow(self):
        """加载ComfyUI工作流JSON文件"""
        try:
            with open(self.workflow_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载工作流文件失败: {str(e)}")
            return None
    
    def update_workflow_params(self, workflow, params):
        """更新工作流参数
        
        Args:
            workflow: 工作流JSON对象
            params: 要更新的参数字典，包含start_image, end_image, description等
            
        Returns:
            更新后的工作流JSON对象
        """
        # 查找并更新229号节点的output_file_path为当前文件夹
        if '229' in workflow:
            node = workflow['229']
            if 'inputs' in node:
                # 获取当前工作目录
                current_dir = os.getcwd()
                node['inputs']['output_file_path'] = current_dir
                print(f"已将229号节点的output_file_path设置为: {current_dir}")
        
        # 查找并更新起始图片节点
        for node_id, node in workflow.items():
            if node['class_type'] == 'LoadImage' and 'image' in node['inputs'] and node.get('_meta', {}).get('title') == '首帧':
                # 设置起始图片路径
                node['inputs']['image'] = params['start_image']
                break
        
        # 查找并更新结束图片节点
        for node_id, node in workflow.items():
            if node['class_type'] == 'LoadImage' and 'image' in node['inputs'] and node.get('_meta', {}).get('title') == '尾帧':
                # 设置结束图片路径
                node['inputs']['image'] = params['end_image']
                break
        
        # 查找并更新描述文本节点
        for node_id, node in workflow.items():
            if node['class_type'] == 'easy prompt' and 'text' in node['inputs']:
                # 设置描述文本
                node['inputs']['text'] = params['description']
                break
        
        # 查找并更新240号节点的text项为旁白内容
        if '240' in workflow and 'narration' in params:
            node = workflow['240']
            if 'inputs' in node and 'text' in node['inputs']:
                node['inputs']['text'] = params['narration']
                print(f"已将240号节点的text项设置为旁白内容")
        
        # 查找所有class_type为Text Overlay的节点，将旁白内容传入其text属性
        if 'narration' in params:
            for node_id, node in workflow.items():
                if node.get('class_type') == 'Text Overlay' and 'inputs' in node and 'text' in node['inputs']:
                    node['inputs']['text'] = params['narration']
                    print(f"已将节点 {node_id} (Text Overlay) 的text属性设置为旁白内容")
        
        return workflow
    
    def call_comfyui_api(self, workflow):
        """调用ComfyUI API执行工作流
        
        Args:
            workflow: 完整的工作流JSON对象
            
        Returns:
            API响应结果
        """
        url = f"{self.api_base}/prompt"
        
        try:
            # 构建请求参数
            payload = {
                "prompt": workflow,
                "output_dir": self.output_dir
            }
            
            # 发送请求
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                # 轮询任务状态，直到完成
                if 'prompt_id' in result:
                    completed = self._wait_for_completion(result['prompt_id'])
                    if not completed:
                        print("任务未在超时时间内完成")
                        return None
                return result
            else:
                print(f"API调用失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
                
        except Exception as e:
            print(f"调用ComfyUI API时出错: {str(e)}")
            return None
    
    def _wait_for_completion(self, prompt_id):
        """等待任务完成
        
        Args:
            prompt_id: 任务ID
        """
        url = f"{self.api_base}/history/{prompt_id}"
        
        print(f"开始等待任务 {prompt_id} 完成...")
        start_time = time.time()
        timeout = 300  # 5分钟超时
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    history = response.json()
                    if prompt_id in history:
                        # 检查任务是否有输出（表示已完成）
                        if 'outputs' in history[prompt_id]:
                            print(f"任务 {prompt_id} 已完成，发现输出结果")
                            # 等待5秒确保文件写入完成
                            print("等待5秒确保视频文件完全写入...")
                            time.sleep(5)
                            return True
                time.sleep(3)  # 每3秒检查一次
            except Exception as e:
                print(f"检查任务状态时出错: {str(e)}")
                time.sleep(3)
        
        print(f"任务 {prompt_id} 等待超时")
        return False
    
    def generate_video(self, config_row):
        """根据配置生成单个视频"""
        if not config_row['是否生效']:
            return None
        
        sequence_id = config_row['序号']
        print(f"处理序号 {sequence_id} 的视频")
        
        try:
            # 清空outpaths.txt文件的内容
            outpaths_file = "outpaths.txt"
            with open(outpaths_file, 'w', encoding='utf-8') as f:
                f.write('')
            print(f"已清空outpaths.txt文件")
            
            # 获取图片路径
            start_image = str(config_row['首帧'])
            end_image = str(config_row['尾帧'])
            
            # 转换为绝对路径
            start_image = os.path.abspath(os.path.join(self.image_dir, start_image))
            end_image = os.path.abspath(os.path.join(self.image_dir, end_image))
            
            # 验证图片文件是否存在
            if not os.path.exists(start_image):
                print(f"错误：首帧图片 '{start_image}' 不存在")
                return None
            if not os.path.exists(end_image):
                print(f"错误：尾帧图片 '{end_image}' 不存在")
                return None
            
            # 构建参数
            params = {
                "start_image": start_image,
                "end_image": end_image,
                "description": str(config_row['画面镜头描述']),
                "sequence_id": str(sequence_id)
            }
            
            # 检查是否有“旁白”列
            if '旁白' in config_row:
                params['narration'] = str(config_row['旁白'])
                print(f"获取旁白内容: {params['narration']}")
            
            # 加载工作流
            workflow = self.load_workflow()
            if not workflow:
                return None
            
            # 更新工作流参数
            updated_workflow = self.update_workflow_params(workflow, params)
            
            # 调用ComfyUI API
            result = self.call_comfyui_api(updated_workflow)
            
            if not result:
                print("工作流调用失败")
                return None
            
            # 处理工作流结果
            return self._process_workflow_result(result, sequence_id)
            
        except Exception as e:
            print(f"生成视频时出错: {str(e)}")
            return None
    
    def _process_workflow_result(self, result, sequence_id):
        """处理工作流返回结果"""
        print(f"API返回结果: {result}")
        
        try:
            if isinstance(result, dict):
                # ComfyUI API通常返回prompt_id和其他信息
                if 'prompt_id' in result:
                    prompt_id = result['prompt_id']
                    print(f"工作流执行成功，prompt_id: {prompt_id}")
                    
                    # 从ComfyUI历史记录中获取生成的视频文件名
                    video_path = self._get_video_from_history(prompt_id, sequence_id)
                    
                    if video_path:
                        print(f"视频生成成功，保存路径: {video_path}")
                        return {'sequence_id': sequence_id, 'video_path': video_path, 'status': 'success'}
                    else:
                        print(f"视频文件未找到，可能正在生成中")
                        return {'sequence_id': sequence_id, 'video_path': None, 'status': 'pending'}
                else:
                    error_msg = result.get('message', 'API调用失败')
                    print(f"工作流执行失败: {error_msg}")
                    return {'sequence_id': sequence_id, 'video_path': None, 'status': 'failed', 'error_msg': error_msg}
            else:
                error_msg = "API返回结果格式错误"
                print(f"{error_msg}: {result}")
                return {'sequence_id': sequence_id, 'video_path': None, 'status': 'failed', 'error_msg': error_msg}
        except Exception as e:
            error_msg = f"处理工作流结果时出错: {str(e)}"
            print(error_msg)
            return {'sequence_id': sequence_id, 'video_path': None, 'status': 'failed', 'error_msg': error_msg}
    
    def _get_video_from_history(self, prompt_id, sequence_id):
        """从outpaths.txt文件中获取视频文件并拷贝到output_videos文件夹
        
        Args:
            prompt_id: 任务ID
            sequence_id: 序列ID
            
        Returns:
            视频文件路径
        """
        try:
            # 读取outpaths.txt文件获取视频地址
            outpaths_file = "outpaths.txt"
            video_file = None
            
            if os.path.exists(outpaths_file):
                # 检查文件大小
                file_size = os.path.getsize(outpaths_file)
                print(f"outpaths.txt文件大小: {file_size} 字节")
                
                with open(outpaths_file, 'r', encoding='utf-8') as f:
                    video_file = f.read().strip()
                
                print(f"从outpaths.txt获取视频地址: '{video_file}'")
                
                # 验证文件是否存在
                if video_file and os.path.exists(video_file):
                    # 构建目标路径
                    base_name = f"video_{sequence_id}"
                    extension = ".mp4"
                    target_file = os.path.join(self.output_dir, f"{base_name}{extension}")
                    
                    # 容错处理：如果文件已存在，增加数字编号后缀
                    counter = 1
                    while os.path.exists(target_file):
                        print(f"目标文件已存在: {target_file}")
                        target_file = os.path.join(self.output_dir, f"{base_name}_{counter}{extension}")
                        counter += 1
                    
                    # 拷贝文件
                    import shutil
                    shutil.copy2(video_file, target_file)
                    print(f"视频已拷贝到: {target_file}")
                    return target_file
                else:
                    print(f"视频文件不存在或路径为空: '{video_file}'")
            else:
                print(f"outpaths.txt文件不存在")
                
                # 如果outpaths.txt不存在，尝试从历史记录中获取
                url = f"{self.api_base}/history/{prompt_id}"
                response = requests.get(url)
                if response.status_code == 200:
                    history = response.json()
                    if prompt_id in history:
                        outputs = history[prompt_id].get('outputs', {})
                        print(f"历史记录中的输出节点数量: {len(outputs)}")
                        
                        # 直接查找218号节点的输出
                        if '218' in outputs:
                            node_output = outputs['218']
                            # 检查节点类型确认是VHS_SelectFilename
                            node_info = node_output.get('node', {})
                            if node_info.get('class_type') == 'VHS_SelectFilename':
                                # 从节点输出获取视频文件路径
                                # 直接获取'Filename'键的值，这是完整的文件地址
                                if 'Filename' in node_output:
                                    video_file = node_output['Filename']
                                    print(f"从218号节点获取视频地址: {video_file}")
                                    
                                    # 验证文件是否存在
                                    if os.path.exists(video_file):
                                        # 构建目标路径
                                        base_name = f"video_{sequence_id}"
                                        extension = ".mp4"
                                        target_file = os.path.join(self.output_dir, f"{base_name}{extension}")
                                        
                                        # 容错处理：如果文件已存在，增加数字编号后缀
                                        counter = 1
                                        while os.path.exists(target_file):
                                            print(f"目标文件已存在: {target_file}")
                                            target_file = os.path.join(self.output_dir, f"{base_name}_{counter}{extension}")
                                            counter += 1
                                        
                                        # 拷贝文件
                                        import shutil
                                        shutil.copy2(video_file, target_file)
                                        print(f"视频已拷贝到: {target_file}")
                                        return target_file
                                    else:
                                        print(f"视频文件不存在: {video_file}")
                        else:
                            print("218号节点不存在于历史记录中")
                    else:
                        print(f"历史记录中未找到prompt_id: {prompt_id}")
                else:
                    print(f"获取历史记录失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"获取视频文件时出错: {str(e)}")
        
        return None
    
    def process_all(self, excel_path, process_mode='all', output_excel_path=None):
        """处理Excel中的记录
        
        Args:
            excel_path: 配置Excel文件路径
            process_mode: 处理模式，'all'表示处理所有记录，'failed'表示只处理失败的记录
            output_excel_path: 输出Excel文件路径，当process_mode为'failed'时使用
        """
        # 加载配置
        df = self.load_excel_config(excel_path)
        if df is None:
            return
        
        # 验证配置
        if not self.validate_config(df):
            return
        
        # 准备存储所有结果的列表
        all_results = []
        
        # 检查是否生效列的数据类型
        is_bool_column = isinstance(df['是否生效'].iloc[0], bool)
        
        # 处理模式选择
        if process_mode == 'failed':
            # 只处理失败的记录
            if not output_excel_path or not os.path.exists(output_excel_path):
                print(f"错误：output.xlsx 文件不存在，无法处理失败记录")
                return
            
            # 加载output.xlsx文件
            try:
                output_df = pd.read_excel(output_excel_path)
                # 获取失败的记录（视频地址为空或包含失败原因的记录）
                failed_records = output_df[
                    (output_df['视频路径'].isna()) | 
                    (output_df['视频路径'] == '') | 
                    (output_df.get('失败原因', pd.Series([False]*len(output_df))).notna())
                ]
                
                if failed_records.empty:
                    print("没有失败的记录需要重新处理")
                    return
                
                # 提取失败记录的id
                failed_ids = set(failed_records['id'].astype(str))
                print(f"找到 {len(failed_ids)} 条失败记录需要重新处理")
                
                # 过滤配置文件中的记录，只保留失败的记录
                df = df[df['序号'].astype(str).isin(failed_ids)]
                valid_count = sum(1 for _, row in df.iterrows() if row['是否生效'])
                
                if valid_count == 0:
                    print("没有有效的失败记录需要处理")
                    return
                
                print(f"开始处理有效失败记录，共 {valid_count} 条")
                
            except Exception as e:
                print(f"读取output.xlsx文件失败: {str(e)}")
                return
        else:
            # 处理所有记录
            valid_count = sum(1 for _, row in df.iterrows() if row['是否生效'])
            print(f"开始处理所有有效记录，共 {valid_count} 条")
        
        # 处理每条记录
        success_count = 0
        fail_count = 0
        pending_count = 0
        
        for index, row in df.iterrows():
            # 生成视频
            result = self.generate_video(row)
            
            # 处理返回结果
            if result and isinstance(result, dict) and 'sequence_id' in result:
                # 无论成功失败都添加到结果列表
                if result.get('status') == 'success' and result.get('video_path'):
                    success_count += 1
                    # 成功记录只包含id和视频路径
                    all_results.append({
                        'id': result['sequence_id'],
                        '视频路径': result['video_path']
                    })
                elif result.get('status') == 'pending':
                    pending_count += 1
                    # 待处理记录
                    all_results.append({
                        'id': result['sequence_id'],
                        '视频路径': result.get('video_path', ''),
                        '状态': '处理中'
                    })
                else:
                    fail_count += 1
                    # 失败记录包含id和失败原因
                    error_msg = result.get('error_msg', '未知错误')
                    all_results.append({
                        'id': result['sequence_id'],
                        '视频路径': '',
                        '失败原因': error_msg
                    })
            
            # 如果不是最后一条记录且当前记录有效，等待几秒再处理下一条
            is_last_row = (index == len(df) - 1)
            is_valid_row = row['是否生效'] if is_bool_column else row['是否生效'] == 'TRUE'
            
            if not is_last_row and is_valid_row:
                time.sleep(3)
        
        # 保存结果
        if all_results:
            # 构建output.xlsx的保存路径
            output_path = os.path.join(self.output_dir, 'output.xlsx')
            
            if process_mode == 'failed' and output_excel_path and os.path.exists(output_excel_path):
                # 更新现有的output.xlsx文件
                try:
                    output_df = pd.read_excel(output_excel_path)
                    
                    # 将all_results转换为字典，方便查找
                    result_dict = {str(item['id']): item for item in all_results}
                    
                    # 更新output_df中对应的行
                    for idx, row in output_df.iterrows():
                        row_id = str(row['id'])
                        if row_id in result_dict:
                            if '视频路径' in result_dict[row_id]:
                                output_df.at[idx, '视频路径'] = result_dict[row_id]['视频路径']
                            if '失败原因' in result_dict[row_id]:
                                output_df.at[idx, '失败原因'] = result_dict[row_id]['失败原因']
                            if '状态' in result_dict[row_id]:
                                output_df.at[idx, '状态'] = result_dict[row_id]['状态']
                    
                    # 保存更新后的文件
                    output_df.to_excel(output_path, index=False)
                    print(f"已更新失败记录到: {output_path}")
                except Exception as e:
                    print(f"更新output.xlsx文件失败: {str(e)}")
                    # 如果更新失败，尝试直接保存结果
                    result_df = pd.DataFrame(all_results)
                    result_df.to_excel(output_path, index=False)
                    print(f"结果已保存到: {output_path}")
            else:
                # 创建新的output.xlsx文件
                result_df = pd.DataFrame(all_results)
                result_df.to_excel(output_path, index=False)
                print(f"结果已保存到: {output_path}")
        
        print(f"处理完成: 总记录 {len(df)}, 有效 {valid_count}, 成功 {success_count}, 失败 {fail_count}, 处理中 {pending_count}")

def main():
    """主函数"""
    print("=== ComfyUI视频生成器 ===")
    print("本程序将读取Excel配置文件，并使用ComfyUI工作流生成视频")
    print("注意：请确保ComfyUI服务器正在运行")
    
    # 使用示例配置文件作为默认
    excel_path = sys.argv[1] if len(sys.argv) > 1 else "示例配置文件.xlsx"
    
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        print(f"错误：文件 '{excel_path}' 不存在")
        return
    
    # 询问用户处理模式
    print("\n请选择处理模式：")
    print("1. 按照配置文件重新生成所有视频")
    print("2. 只生成output.xlsx中记录为失败的项目")
    
    # 获取用户输入
    choice = input("请输入选择 (1 或 2): ").strip()
    
    # 创建生成器实例，传递表格文件名
    generator = ComfyUIVideoGenerator(excel_path)
    
    # 构建output.xlsx的保存路径
    output_excel_path = os.path.join(generator.output_dir, 'output.xlsx')
    
    # 根据用户选择执行不同的处理逻辑
    if choice == '2':
        # 检查output.xlsx是否存在
        if not os.path.exists(output_excel_path):
            print(f"错误：{output_excel_path} 文件不存在，请先运行选项1生成初始结果")
            return
        
        # 只处理失败的记录
        generator.process_all(excel_path, process_mode='failed', output_excel_path=output_excel_path)
    else:
        # 默认处理所有记录
        generator.process_all(excel_path)

if __name__ == "__main__":
    main()