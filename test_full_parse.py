import pandas as pd
import app as myapp

# 模拟 /api/upload 中的加载
df = pd.read_excel('EXPORT_20260520134027.xlsx')

# 过滤汇总行（模拟代码逻辑）
df = df[df['Sales Document'].notna()].reset_index(drop=True)

# 应用 Material Description 解析
if 'Material Description' in df.columns:
    df[['Parsed_Product', 'Parsed_Drawing', 'Parsed_Spec', 'Parsed_Alloy', 'Parsed_ItemCat', 'Parsed_Length']] = \
        df['Material Description'].apply(myapp.split_material_description)

print('源文件1导入后列名:')
cols = list(df.columns)
for i, c in enumerate(cols):
    print(f'  {i}: {c}')
print()
print(f'新增6列位置:')
print(f'  {cols.index("Parsed_Product")}: Parsed_Product')
print(f'  {cols.index("Parsed_Drawing")}: Parsed_Drawing')
print(f'  {cols.index("Parsed_Spec")}: Parsed_Spec')
print(f'  {cols.index("Parsed_Alloy")}: Parsed_Alloy')
print(f'  {cols.index("Parsed_ItemCat")}: Parsed_ItemCat')
print(f'  {cols.index("Parsed_Length")}: Parsed_Length')

print()
print('源文件1导入后前50行（6列新增字段）:')
print('=' * 200)
for i in range(min(50, len(df))):
    row = df.iloc[i]
    md = row['Material Description']
    print(f'{i+1:2}. {md}')
    print(f'    -> Product:  {row["Parsed_Product"]}')
    print(f'    -> Drawing:  {row["Parsed_Drawing"]}')
    print(f'    -> Spec.:    {row["Parsed_Spec"]}')
    print(f'    -> Alloy:    {row["Parsed_Alloy"]}')
    print(f'    -> Item Cat: {row["Parsed_ItemCat"]}')
    print(f'    -> Length:   {row["Parsed_Length"]}')
    print('-' * 200)
print(f'总行数: {len(df)}')
