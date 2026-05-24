samples = [
    'FPDT_8X1_8X1-ZN-JUMBO_300370_O',
    'FPDT_6.35X1_6.35X1-ZN-JUMBO_300370_O',
    'FPDT_9.52X0.71_9.52X0.71-COIL_300370_O',
    'FMPE_TES9001_MPC_1729.2MM_3003_H112',
    'FPDT_9.53X1.24_9.53X1.24X119MM*-CTL_3003'
]

for desc in samples:
    parts = str(desc).split('_')
    product = parts[0] if len(parts) > 0 else ''
    drawing = parts[1] if len(parts) > 1 and product == 'FMPE' else ''
    
    # Item Cat: 含-ZN后缀时=Product-ZN, 否则=Product
    has_zn = '-ZN' in desc or '-zn' in desc
    item_cat = product + '-ZN' if has_zn else product
    
    length = 'coil' if 'coil' in str(desc).lower() else 'CTL'
    
    print('原始:', desc)
    print('  含-ZN?:', has_zn)
    print('  Product:', product)
    print('  Drawing:', drawing)
    print('  Item Cat:', item_cat, '  (Product-ZN if has ZN)')
    print('  Length:', length)
    print('---')

