# ComfyUI视频生成器

这是一个基于Python的视频生成应用，可以读取Excel配置文件中的信息，并使用ComfyUI工作流生成视频。

## 功能特点

- 读取Excel配置文件中的每一行信息（序号、首帧、尾帧、画面镜头描述和是否生效）
- 根据配置调用ComfyUI工作流API生成视频
- 逐个处理每一行记录并输出生成的视频
- 支持跳过未生效的记录
- 支持重新处理失败的记录
- 自动将生成的视频保存在output_videos文件夹中
- 支持自定义ComfyUI工作流参数

## 安装依赖

1. 确保已安装Python 3.8+
2. 安装所需的Python库：

```bash
pip install -r requirements.txt
```

## 配置说明

1. **配置环境变量**：
   - 复制`.env.example`文件为`.env`
   - 修改`COMFYUI_API_BASE`为实际的ComfyUI API地址（默认：http://localhost:8188）
   - 修改`COMFYUI_WORKFLOW_JSON`为ComfyUI工作流JSON文件路径（默认：workflow.json）

2. **配置ComfyUI工作流**：
   - 确保ComfyUI服务器正在运行
   - 在ComfyUI界面中创建并配置您的视频生成工作流
   - 导出工作流为JSON文件（使用ComfyUI界面中的"Save workflow as"功能）
   - 将导出的JSON文件保存为`workflow.json`（或在.env中配置自定义文件名）
   - 确保工作流中包含处理起始图片、结束图片和文本描述的节点
   - 根据您的工作流节点结构，可能需要修改`comfyui_video_generator.py`中的`update_workflow_params`方法

3. **准备Excel配置文件**：
   - Excel文件必须包含以下列：
     - 序号：视频的唯一标识符
     - 首帧：起始图片的路径（可以是绝对路径或相对于images文件夹的路径）
     - 尾帧：结束图片的路径（可以是绝对路径或相对于images文件夹的路径）
     - 画面镜头描述：对要生成画面的文字描述
     - 是否生效：布尔值，控制是否生成该视频
   - 可以参考提供的`示例配置文件.xlsx`

## 使用方法

### 方法一：使用批处理文件（Windows）

1. 确保已安装依赖并完成配置
2. 双击运行`生成_ComfyUI.bat`文件
3. 根据提示输入Excel配置文件的路径
4. 程序将开始处理每条记录并生成视频
5. 生成的视频将保存在`output_videos`文件夹中

### 方法二：直接运行Python脚本

1. 确保已安装依赖并完成配置
2. 运行主程序：

```bash
python comfyui_video_generator.py
```

3. 根据提示选择处理模式：
   - 选项1：处理所有有效记录
   - 选项2：只处理失败的记录
4. 如果选择了处理模式1，程序将开始处理所有有效记录
5. 如果选择了处理模式2，程序将重新处理上一次运行中失败的记录
6. 生成的视频将保存在`output_videos`文件夹中，结果将记录在`output.xlsx`文件中

## 注意事项

1. 请确保ComfyUI服务正在运行且可访问
2. 处理大量视频时可能需要较长时间，请耐心等待
3. 程序会在API调用之间等待3秒，以避免请求过于频繁
4. 如遇到API调用失败，程序会继续尝试处理下一条记录
5. 请将所有图片文件放在`images`文件夹中，或在Excel中提供完整的绝对路径
6. 程序会自动验证图片文件是否存在，不存在的图片会导致对应记录处理失败
7. 默认的`workflow.json`是一个示例，您需要根据实际使用的ComfyUI工作流进行配置
8. ComfyUI的工作流JSON格式可能会根据ComfyUI版本有所变化，请确保使用与您ComfyUI版本兼容的工作流JSON

## 文件结构

- `comfyui_video_generator.py`：基于ComfyUI的视频生成主程序文件
- `kouzi_video_generator.py`：基于扣子API的视频生成程序（旧版）
- `video_generator.py`：基于Skyreels的视频生成程序（旧版）
- `workflow.json`：ComfyUI工作流配置文件（示例）
- `create_example_excel.py`：创建示例Excel配置文件的脚本
- `requirements.txt`：所需Python库清单
- `.env` 和 `.env.example`：环境变量配置文件
- `示例配置文件.xlsx`：示例Excel配置文件
- `images/`：存放首帧和尾帧图片的文件夹
- `output_videos/`：生成的视频保存目录（程序会自动创建）
- `生成_ComfyUI.bat`：Windows批处理文件，用于快速运行程序

## 工作流配置指南

1. **修改工作流JSON**：
   - 在ComfyUI中创建您的视频生成工作流
   - 确保工作流包含：
     - 至少两个LoadImage节点（用于首帧和尾帧）
     - 一个TextEncode或类似节点（用于接收画面描述）
     - 一个视频生成节点（如ImageToVideo或类似节点）
     - 一个SaveVideo或类似节点（用于保存生成的视频）

2. **更新程序中的工作流参数映射**：
   - 打开`comfyui_video_generator.py`文件
   - 找到`update_workflow_params`方法
   - 根据您的工作流节点ID和参数名，修改方法中的代码，确保正确映射首帧、尾帧和描述文本

## 故障排除

1. **Excel文件读取失败**：
   - 检查文件路径是否正确
   - 确保文件格式为.xlsx
   - 验证文件是否包含所有必要的列

2. **API调用失败**：
   - 检查`.env`文件中的API地址是否正确
   - 确保ComfyUI服务正在运行
   - 查看错误信息以获取更多详情
   - 检查ComfyUI的日志文件以获取更多调试信息

3. **依赖安装问题**：
   - 确保pip版本为最新
   - 尝试使用虚拟环境安装依赖

4. **图片文件错误**：
   - 确保所有首帧和尾帧图片文件存在
   - 检查图片路径是否正确
   - 如果使用相对路径，请确保图片放在`images`文件夹中

5. **工作流执行失败**：
   - 检查工作流JSON文件是否格式正确
   - 确保工作流中所有必要的节点和连接都已正确配置
   - 检查ComfyUI是否有足够的资源（内存、GPU等）
   - 查看ComfyUI的日志以获取详细的错误信息

6. **视频生成但未保存**：
   - 检查工作流中的SaveVideo节点配置
   - 确保output_videos文件夹存在且可写入
   - 检查程序中的`_process_workflow_result`方法，确保视频文件路径配置正确