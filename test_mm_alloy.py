import pandas as pd

samples = [
    'FMPE_NXZ9004_H58A_MPC_549.0MM_119761_H11',
    'FMPE_TES9001_MPC_1729.2MM_3003_H112',
    'FMPE_FHT9002_MPC_669.8MM_9153A_H112',
    'FPDT_16X1.5/N2_16X1.5X3000MM*_CTL_310377',
    'FPDT_9.53X1.24_9.53X1.24X119MM*_CTL_3003',
    'FPDT_12.7X1.2_12.7X1.2-COIL_300370_H112',
    'FMPE_ZKL9007_1000.0MM_310201_F',
    'FPDT_8X1_8X1-ZN-JUMBO_300370_O',
]

print('MM_ 作为 Alloy 分界符验证:')
print('=' * 150)

for desc in samples:
    original = desc
    product_end = desc.find('_')
    product = desc[:product_end] if product_end > 0 else desc
    
    # Drawing (FMPE取第2段)
    parts = desc.split('_')
    drawing = parts[1] if len(parts) > 1 and product == 'FMPE' else ''
    
    # 新逻辑: MM_ 之前是Spec.，之后是Alloy
    alloy = ''
    spec = ''
    
    # 找 'MM_' 或 'MM*_' 的位置作为分界
    import re
    # 匹配 MM后面可能有*，再跟下划线的模式: MM_ / MM*_
    mm_match = re.search(r'(MM\*?_)(.*)', desc)
    if mm_match:
        split_pos = mm_match.start(1) + len(mm_match.group(1))
        # Spec截止到MM_后面之前的下划线，Alloy从那里开始
        # 实际上从原始串最后一个下划线往前找更简单
        alloy = mm_match.group(2)  # MM_之后的所有内容
        # 重新构造 spec: product之后到 alloy之前
        if alloy in desc:
            alloy_idx = desc.rfind(alloy)
            spec_part = desc[product_end+1:alloy_idx]  # product后面到Alloy之前
            if spec_part.endswith('_'):
                spec_part = spec_part[:-1]
            spec = spec_part
    else:
        # 找不到MM标记的回退逻辑
        alloy = parts[-1]
        spec = '_'.join(parts[1:-1]) if len(parts)>=3 else ''
    
    # Length coil/CTL
    length = 'coil' if 'coil' in desc.lower() else 'CTL'
    
    # Item Cat ZN后缀
    item_cat = product + '-ZN' if '-ZN' in desc else product
    
    print(f'原始: {desc}')
    print(f'  -> Product:  {product}')
    print(f'  -> Drawing:  {drawing}')
    print(f'  -> Spec.:    {spec}')
    print(f'  -> Alloy:    {alloy}')
    print(f'  -> Item Cat: {item_cat}')
    print(f'  -> Length:   {length}')
    print('-' * 150)
