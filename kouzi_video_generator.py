import os
import sys
import time
import json
import pandas as pd
import subprocess
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 扣子API配置
coze_api_token = os.getenv("COZE_API_TOKEN", "pat_default_token")
coze_api_base = "https://api.coze.cn"
workflow_id = "7561645381449629738"

def call_coze_workflow(workflow_id, params, api_key=None):
    """调用扣子工作流API"""
    if not api_key:
        api_key = coze_api_token
    
    # 使用正确的扣子工作流API路径
    url = f"{coze_api_base}/v1/workflow/run"
    
    try:
        # 构建正确的请求参数格式
        workflow_params = {
            "workflow_id": workflow_id,
            "parameters": params,

        }
        
        # 执行curl命令
        curl_cmd = [
            "curl",
            "-X", "POST",
            url,
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(workflow_params, ensure_ascii=False)
        ]
        
        # 打印完整的curl命令
        print(f"执行curl命令: {' '.join(curl_cmd)}")
        
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"curl执行失败，退出码: {result.returncode}")
            print(f"curl错误输出: {result.stderr}")
            return None
        
        try:
            response_json = json.loads(result.stdout)
            if isinstance(response_json, dict) and response_json.get('code') != 0:
                print(f"API错误: {response_json.get('msg', 'Unknown error')}")
                # 打印详细的错误信息
                if 'details' in response_json:
                    print(f"错误详情: {json.dumps(response_json['details'], ensure_ascii=False)}")
            return response_json
        except json.JSONDecodeError:
            print(f"无法解析响应为JSON: {result.stdout}")
            return None
    except Exception as e:
        print(f"调用API时出错: {str(e)}")
        return None

class KouziVideoGenerator:
    def __init__(self):
        """初始化视频生成器"""
        self.workflow_id = workflow_id
    
    def load_excel_config(self, excel_path):
        """加载Excel配置文件"""
        try:
            return pd.read_excel(excel_path)
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
    
    def generate_video(self, config_row):
        """根据配置生成单个视频"""
        if not config_row['是否生效']:
            return None
        
        sequence_id = config_row['序号']
        print(f"处理序号 {sequence_id} 的视频")
        
        try:
            # 直接使用Excel中提供的图片链接
            start_image_url = str(config_row['首帧'])
            end_image_url = str(config_row['尾帧'])
            
            # 验证URL格式
            if not start_image_url.startswith(('http://', 'https://')) or not end_image_url.startswith(('http://', 'https://')):
                print(f"错误：图片链接格式无效")
                return None
            
            # 构建工作流参数 - 保持参数名称与工作流要求一致
            params = {
                "start_image": start_image_url,
                "end_image": end_image_url,
                "description": str(config_row['画面镜头描述']),
                "sequence_id": str(sequence_id)
            }
            
            # 调用扣子工作流
            result = call_coze_workflow(self.workflow_id, params)
            
            if not result:
                print("工作流调用失败")
                return None
            
            # 处理工作流结果
            return self._process_workflow_result(result, sequence_id)
            
        except Exception as e:
            print(f"生成视频时出错: {str(e)}")
            return None
    
    def _process_workflow_result(self, result, sequence_id):
        """处理工作流返回结果，提取video字段，使用sequence_id作为id"""
        # 打印完整返回结果进行调试
        print(f"API返回结果: {result}")
        
        try:
            if isinstance(result, dict):
                # 检查是否成功执行
                if result.get('code') == 0:
                    # 打印返回结果中的键，用于调试
                    print(f"返回结果中的键: {list(result.keys())}")
                    
                    # 从data字段获取video信息（data可能是JSON字符串）
                    data = result.get('data')
                    video_url = None
                    
                    if isinstance(data, str):
                        # 尝试解析JSON字符串
                        try:
                            import json
                            data_json = json.loads(data)
                            video_url = data_json.get('video')
                        except json.JSONDecodeError:
                            print(f"data字段不是有效的JSON字符串: {data}")
                    elif isinstance(data, dict):
                        # 如果data已经是字典
                        video_url = data.get('video')
                    
                    # 也检查result根级别是否有video字段
                    if video_url is None:
                        video_url = result.get('video')
                    
                    if video_url is not None:
                        print(f"提取到sequence_id: {sequence_id}, 视频URL: {video_url}")
                        return {'sequence_id': sequence_id, 'video_url': video_url, 'status': 'success'}
                    else:
                        # 代码为0但没有视频URL
                        error_msg = result.get('msg', 'API返回成功但未找到视频URL')
                        print(f"视频生成失败: {error_msg}")
                        return {'sequence_id': sequence_id, 'video_url': None, 'status': 'failed', 'error_msg': error_msg}
                else:
                    # 工作流执行失败
                    error_msg = result.get('msg', 'API调用失败')
                    print(f"工作流执行失败: {error_msg}")
                    print(f"返回结果中的键: {list(result.keys())}")
                    return {'sequence_id': sequence_id, 'video_url': None, 'status': 'failed', 'error_msg': error_msg}
            else:
                error_msg = "API返回结果格式错误"
                print(f"{error_msg}: {result}")
                return {'sequence_id': sequence_id, 'video_url': None, 'status': 'failed', 'error_msg': error_msg}
        except Exception as e:
            error_msg = f"处理工作流结果时出错: {str(e)}"
            print(error_msg)
            return {'sequence_id': sequence_id, 'video_url': None, 'status': 'failed', 'error_msg': error_msg}
        return {'sequence_id': sequence_id, 'video_url': None, 'status': 'failed', 'error_msg': '未知错误'}
    
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
                    (output_df['视频地址'].isna()) | 
                    (output_df['视频地址'] == '') | 
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
                valid_count = sum(df['是否生效'] if is_bool_column else df['是否生效'] == 'TRUE')
                
                if valid_count == 0:
                    print("没有有效的失败记录需要处理")
                    return
                
                print(f"开始处理有效失败记录，共 {valid_count} 条")
                
            except Exception as e:
                print(f"读取output.xlsx文件失败: {str(e)}")
                return
        else:
            # 处理所有记录
            valid_count = sum(df['是否生效'] if is_bool_column else df['是否生效'] == 'TRUE')
            print(f"开始处理所有有效记录，共 {valid_count} 条")
        
        # 处理每条记录
        success_count = 0
        fail_count = 0
        
        for index, row in df.iterrows():
            # 生成视频
            result = self.generate_video(row)
            
            # 处理返回结果
            if result and isinstance(result, dict) and 'sequence_id' in result:
                # 无论成功失败都添加到结果列表
                if result.get('status') == 'success' and result.get('video_url'):
                    success_count += 1
                    # 成功记录只包含id和视频地址
                    all_results.append({
                        'id': result['sequence_id'],
                        '视频地址': result['video_url']
                    })
                else:
                    fail_count += 1
                    # 失败记录包含id和失败原因
                    error_msg = result.get('error_msg', '未知错误')
                    all_results.append({
                        'id': result['sequence_id'],
                        '视频地址': '',
                        '失败原因': error_msg
                    })
            
            # 如果不是最后一条记录且当前记录有效，等待几秒再处理下一条
            is_last_row = (index == len(df) - 1)
            is_valid_row = row['是否生效'] if is_bool_column else row['是否生效'] == 'TRUE'
            
            if not is_last_row and is_valid_row:
                time.sleep(3)
        
        # 保存结果
        if all_results:
            output_path = 'output.xlsx'
            
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
                            if '视频地址' in result_dict[row_id]:
                                output_df.at[idx, '视频地址'] = result_dict[row_id]['视频地址']
                            if '失败原因' in result_dict[row_id]:
                                output_df.at[idx, '失败原因'] = result_dict[row_id]['失败原因']
                    
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
        
        print(f"处理完成: 总记录 {len(df)}, 有效 {valid_count}, 成功 {success_count}, 失败 {fail_count}")

def main():
    """主函数"""
    print("扣子视频生成器")
    
    # 使用play1.xlsx作为默认文件
    excel_path = sys.argv[1] if len(sys.argv) > 1 else "play1.xlsx"
    
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        print(f"错误：文件 '{excel_path}' 不存在")
        return
    
    # 询问用户处理模式
    print("请选择处理模式：")
    print("1. 按照配置文件重新生成所有视频")
    print("2. 只生成output.xlsx中记录为失败的项目")
    
    # 获取用户输入
    choice = input("请输入选择 (1 或 2): ").strip()
    
    # 创建生成器实例
    generator = KouziVideoGenerator()
    
    # 根据用户选择执行不同的处理逻辑
    if choice == '2':
        output_excel_path = 'output.xlsx'
        # 检查output.xlsx是否存在
        if not os.path.exists(output_excel_path):
            print(f"错误：output.xlsx 文件不存在，请先运行选项1生成初始结果")
            return
        
        # 只处理失败的记录
        generator.process_all(excel_path, process_mode='failed', output_excel_path=output_excel_path)
    else:
        # 默认处理所有记录
        generator.process_all(excel_path)

if __name__ == "__main__":
    main()