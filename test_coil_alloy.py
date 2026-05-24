import re

samples = [
    # 有 MM_ 的优先
    'FMPE_NXZ9004_H58A_MPC_549.0MM_119761_H11',
    'FPDT_16X1.5/N2_16X1.5X3000MM*_CTL_310377',
    # 没有 MM_ 但有 COIL 的
    'FPDT_12.7X1.2_12.7X1.2-COIL_300370_H112',
    'FPDT_15.88X1.2_15.88X1.2-COIL_300370_H11',
    'FPDT_ACR2012_9.52*0.68X0.3COIL-_300370_O',
    'FPDT_9.52X0.71_9.52X0.71-COIL_300370_O',
    # 都没有的回退
    'FPDT_8X1_8X1-ZN-JUMBO_300370_O',
]

print('优先级 1: MM_ / MM*_  -> 优先级 2: COIL_/COIL-_  -> 回退逻辑')
print('=' * 150)

for desc in samples:
    parts = desc.split('_')
    product = parts[0] if len(parts) > 0 else ''
    
    alloy = ''
    spec = ''
    matched_rule = ''
    
    # 1. 第一优先级: MM_ / MM*_
    mm_match = re.search(r'(MM\*?_)(.*)', desc)
    if mm_match:
        alloy = mm_match.group(2)
        matched_rule = 'MM_'
        if alloy in desc:
            alloy_idx = desc.rfind(alloy)
            product_end = desc.find('_')
            if product_end > 0 and alloy_idx > product_end:
                spec = desc[product_end+1:alloy_idx]
                if spec.endswith('_'):
                    spec = spec[:-1]
                if spec.endswith('-CTL'):
                    spec = spec[:-4]
    else:
        # 2. 第二优先级: COIL-_ 或 COIL_ 作为分界 (COIL后面可能有-再跟_)
        coil_match = re.search(r'(COIL-?_)(.*)', desc)
        if coil_match:
            alloy = coil_match.group(2)
            matched_rule = 'COIL_'
            if alloy in desc:
                alloy_idx = desc.rfind(alloy)
                product_end = desc.find('_')
                if product_end > 0:
                    spec = desc[product_end+1:alloy_idx]
                    if spec.endswith('_'):
                        spec = spec[:-1]
        else:
            # 都没有，回退逻辑
            alloy = parts[-1]
            matched_rule = 'fallback'
            if len(parts) >= 3:
                spec = '_'.join(parts[1:-1])
            if spec.endswith('-CTL'):
                spec = spec[:-4]
    
    item_cat = product + '-ZN' if '-ZN' in desc else product
    length = 'coil' if 'coil' in desc.lower() else 'CTL'
    
    print(f'原始: {desc}')
    print(f'  匹配规则: {matched_rule}')
    print(f'  -> Spec.:  {spec}')
    print(f'  -> Alloy:  {alloy}')
    print(f'  -> Item Cat: {item_cat}')
    print(f'  -> Length:   {length}')
    print('-' * 150)
