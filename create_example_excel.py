import pandas as pd
import os

# 创建示例数据 - 首帧和尾帧现在是图片路径
data = {
    '序号': [1, 2, 3, 4, 5],
    '首帧': ['cat_start.jpg', 'city_start.jpg', 'waterfall_start.jpg', 'beach_start.jpg', 'mountain_start.jpg'],
    '尾帧': ['cat_end.jpg', 'city_end.jpg', 'waterfall_end.jpg', 'beach_end.jpg', 'mountain_end.jpg'],
    '画面镜头描述': [
        '一只小猫在阳光下玩耍，背景是绿色的草地和几棵树',
        '城市夜景，高楼大厦灯火通明，有车流经过',
        '山间瀑布，水流湍急，周围是茂密的森林',
        '海滩日落，金色的阳光洒在海面上，有几只海鸥飞翔',
        '雪山远景，山顶覆盖着白雪，天空湛蓝'
    ],
    '是否生效': [True, True, False, True, True]
}

# 创建DataFrame
df = pd.DataFrame(data)

# 保存为Excel文件
output_path = '示例配置文件.xlsx'
df.to_excel(output_path, index=False, engine='openpyxl')

print(f"已成功创建Excel文件: {os.path.abspath(output_path)}")
print(f"文件包含 {len(df)} 条记录")
print("\n数据预览:")
print(df)