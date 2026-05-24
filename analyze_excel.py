import pandas as pd
import json

def analyze_excel(file_path):
    print(f"\n{'='*60}")
    print(f"分析文件: {file_path}")
    print('='*60)
    
    xl = pd.ExcelFile(file_path)
    print(f"Sheet列表: {xl.sheet_names}")
    
    result = {
        "file": file_path,
        "sheets": {}
    }
    
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"\n--- Sheet: {sheet_name} ---")
        print(f"行数: {len(df)}, 列数: {len(df.columns)}")
        print(f"列名: {list(df.columns)}")
        print(f"\n前5行数据:")
        print(df.head().to_string())
        
        result["sheets"][sheet_name] = {
            "columns": list(df.columns),
            "row_count": len(df),
            "sample_data": df.head().to_dict(orient='records')
        }
    
    return result

# 分析所有文件
files = [
    r"c:\Users\Admin\Documents\trae_projects\trae-03\sales-report\shipment026.xlsx",
    r"c:\Users\Admin\Documents\trae_projects\trae-03\sales-report\EXPORT_20260520134027.xlsx",
    r"c:\Users\Admin\Documents\trae_projects\trae-03\sales-report\EXPORT_20260523063026-turnover.xlsx"
]

all_results = {}
for f in files:
    all_results[f] = analyze_excel(f)

# 保存分析结果
with open('analysis_result.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print("分析完成，结果已保存到 analysis_result.json")
print('='*60)
