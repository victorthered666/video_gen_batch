import os

# 定义文件夹路径
folder_path = "images/liemoren"

# 检查文件夹是否存在
if not os.path.exists(folder_path):
    print(f"文件夹 {folder_path} 不存在")
    exit()

# 获取文件夹中的所有文件
files = os.listdir(folder_path)

# 遍历所有文件
for file in files:
    # 检查是否是图片文件
    if file.endswith(".png"):
        # 分割文件名，去掉take开始的后缀
        parts = file.split("_take_")
        if len(parts) > 1:
            new_filename = parts[0] + ".png"
            old_path = os.path.join(folder_path, file)
            new_path = os.path.join(folder_path, new_filename)
            
            # 重命名文件
            os.rename(old_path, new_path)
            print(f"已将 {file} 重命名为 {new_filename}")

print("重命名完成！")