from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
import io
import json
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR', BASE_DIR)
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(DATA_DIR, 'uploads'))
OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', os.path.join(DATA_DIR, 'output'))
MAPPINGS_FILE = os.environ.get('MAPPINGS_FILE', os.path.join(DATA_DIR, 'saved_mappings.json'))
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def load_saved_mappings():
    if os.path.exists(MAPPINGS_FILE):
        try:
            with open(MAPPINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_mappings_to_file(mappings):
    with open(MAPPINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, ensure_ascii=False, indent=2)

def require_columns(df, required_columns, label):
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        return jsonify({
            'error': f'{label} 缺少必要列: {", ".join(missing)}'
        }), 400
    return None

TARGET_COLUMNS = [
    'Cutomer', 'Ship To', 'Product', 'Customer product', 'Item Cat', 'Drawing', 'Length', 'Cimalex',
    'Spec.', 'Alloy', 'Material', 'Material Description', 'kg', 'PC', 'Goods Mvt Date', 'AV', 'Metal', 'PCS/KG',
    'Weight/PC', 'Unit Price', 'Total', 'Net AV', 'Net AV Total',
    'Net Total', 'Tax Amount', 'Export', 'Sales', 'Invoice', 'Invoice currency', 'Market', 'Delivery No.',
    '-', 'Trading', '月份', '美金汇率'
]

SOURCE1_FIELDS = []
SOURCE2_FIELDS = []
source1_df = None
source2_df = None

def split_material_description(desc):
    if pd.isna(desc):
        return pd.Series(['', '', '', '', '', ''])

    desc = str(desc).strip()

    mpe_idx = desc.find('MPE')
    pdt_idx = desc.find('PDT')
    if mpe_idx == -1 and pdt_idx == -1:
        product = ''
    elif pdt_idx == -1 or (mpe_idx != -1 and mpe_idx < pdt_idx):
        product = 'MPE'
    else:
        product = 'PDT'

    drawing = ''
    acr_match = re.search(r'_(ACR[^_]+)_', desc)
    if acr_match:
        drawing = acr_match.group(1)
    if product == 'MPE' and mpe_idx >= 0 and not drawing:
        rest = desc[mpe_idx + len('MPE'):]
        parts = rest.split('_')
        if len(parts) >= 2:
            drawing = parts[1]

    item_cat = f'{product}-ZN' if product and '-ZN' in desc else product

    if 'coil' in desc.lower():
        length = 'coil'
    elif 'CTL' in desc:
        length = 'CTL'
    else:
        length = 'CTL'

    spec = ''
    alloy = ''

    if product == 'MPE':
        mm_idx = desc.find('MM')
        if mm_idx >= 0:
            before_mm = desc[:mm_idx]
            spec = before_mm.rsplit('_', 1)[-1] if '_' in before_mm else before_mm
            if desc[mm_idx:mm_idx + 3] == 'MM_':
                alloy = desc[mm_idx + 3:]
            else:
                alloy = desc[mm_idx + 2:]
    elif product == 'PDT':
        pdt_start = desc.find('FPDT_')
        if pdt_start >= 0:
            spec_start = pdt_start + len('FPDT_')
            spec_end = -1
            for marker in ['MM', 'COIL-_', '_CTL', '-COIL', '-JUMBO']:
                idx = desc.find(marker, spec_start)
                if idx >= 0:
                    spec_end = idx
                    break
            if spec_end >= 0:
                spec = desc[spec_start:spec_end]
            else:
                spec = desc[spec_start:]

        for marker in ['COIL-_', 'MM_', 'COIL_', 'CTL_', 'JUMBO#_', 'JUMBO_']:
            idx = desc.find(marker)
            if idx >= 0:
                alloy = desc[idx + len(marker):]
                break

    if spec.endswith('_'):
        spec = spec[:-1]
    for tail in ['-COIL-', '-COIL', '-CTL']:
        if spec.endswith(tail):
            spec = spec[:-len(tail)]

    return pd.Series([product, drawing, spec, alloy, item_cat, length])

def safe_convert_value(val):
    if pd.isna(val):
        return ''
    if isinstance(val, pd.Timestamp):
        return val.strftime('%Y-%m-%d') if not pd.isna(val) else ''
    return str(val)

def safe_convert_number(val):
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)) and not pd.isna(val):
        return float(val)
    try:
        return float(str(val).replace(',', '').strip())
    except:
        text = str(val).strip().replace(',', '')
        match = re.search(r'-?\d+(?:\.\d+)?', text)
        if match:
            try:
                return float(match.group(0))
            except:
                return None
        return None

def serialize_dataframe_rows(df):
    records = df.head(5).fillna('').to_dict(orient='records')
    serialized = []
    for record in records:
        clean_record = {}
        for key, value in record.items():
            if isinstance(value, pd.Timestamp):
                clean_record[key] = value.strftime('%Y-%m-%d')
            elif hasattr(value, 'isoformat') and not isinstance(value, (str, bytes)):
                try:
                    clean_record[key] = value.isoformat()
                except:
                    clean_record[key] = str(value)
            else:
                clean_record[key] = value if isinstance(value, (str, int, float, bool)) else str(value)
        serialized.append(clean_record)
    return serialized

def build_report_row(row, source2_row, mappings, source1_df, source2_df, idx, has_source2_match):
    numeric_target_columns = {'Net Total', 'Tax Amount', 'kg', 'PC', 'Metal', 'Weight/PC'}
    new_row = {}
    net_total_num = None
    tax_amount_num = None

    for target_col in TARGET_COLUMNS:
        source_field = mappings.get(target_col)
        val = ''
        if source_field:
            source_is_source2 = source_field in source2_df.columns
            if not has_source2_match and source_is_source2:
                val = ''
            elif source_field in source1_df.columns:
                val = row.get(source_field, '')
            elif source_field in source2_df.columns:
                if source2_row is not None:
                    val = source2_row.get(source_field, '')
                else:
                    val = ''

        if target_col in numeric_target_columns:
            val = safe_convert_number(val)
            if target_col == 'Net Total':
                net_total_num = val
            elif target_col == 'Tax Amount':
                tax_amount_num = val
            if not has_source2_match and source_field and source_field in source2_df.columns:
                new_row[target_col] = None if target_col != 'Total' else ''
                continue

            new_row[target_col] = val
            continue

        if target_col in ['Item Cat', 'Ship To', 'Delivery No.']:
            if pd.notna(val):
                try:
                    val = str(int(float(val)))
                except:
                    val = str(val) if pd.notna(val) else ''
            else:
                val = ''

        new_row[target_col] = safe_convert_value(val)

    total_num = (net_total_num or 0) + (tax_amount_num or 0)
    new_row['Total'] = float(round(total_num, 2)) if (has_source2_match and (net_total_num is not None or tax_amount_num is not None)) else ''
    return new_row

def summarize_source1_by_delivery(df):
    if 'Delivery' not in df.columns:
        return df

    # Keep rows with a delivery number, then merge duplicates into one row per delivery.
    df = df.copy()
    df = df[df['Delivery'].notna()].reset_index(drop=True)

    numeric_cols = [
        col for col in df.columns
        if col != 'Delivery' and pd.api.types.is_numeric_dtype(df[col])
    ]

    def first_non_empty(series):
        for value in series:
            if pd.notna(value) and str(value).strip() != '':
                return value
        return ''

    agg_map = {}
    for col in df.columns:
        if col == 'Delivery':
            continue
        if col in numeric_cols:
            agg_map[col] = 'sum'
        else:
            agg_map[col] = first_non_empty

    grouped = (
        df.sort_values('Delivery')
          .groupby('Delivery', as_index=False, dropna=False)
          .agg(agg_map)
    )

    return grouped

def normalize_string(s):
    return str(s).lower().strip().replace(' ', '').replace('_', '').replace('/', '')

def auto_map_fields():
    saved = load_saved_mappings()
    mappings = {}
    source_fields = SOURCE1_FIELDS + SOURCE2_FIELDS

    # Some business-critical numeric fields should always prefer the source 1
    # columns that carry the actual delivery quantities.
    if 'Shipped Quantity BUOM' in SOURCE1_FIELDS:
        mappings['kg'] = 'Shipped Quantity BUOM'
    if 'Shipped Quantity' in SOURCE1_FIELDS:
        mappings['PC'] = 'Shipped Quantity'
    
    if 'Parsed_Product' in SOURCE1_FIELDS:
        mappings['Product'] = 'Parsed_Product'
    if 'Parsed_Drawing' in SOURCE1_FIELDS:
        mappings['Drawing'] = 'Parsed_Drawing'
    if 'Parsed_Spec' in SOURCE1_FIELDS:
        mappings['Spec.'] = 'Parsed_Spec'
    if 'Parsed_Alloy' in SOURCE1_FIELDS:
        mappings['Alloy'] = 'Parsed_Alloy'
    if 'Parsed_ItemCat' in SOURCE1_FIELDS:
        mappings['Item Cat'] = 'Parsed_ItemCat'
    if 'Parsed_Length' in SOURCE1_FIELDS:
        mappings['Length'] = 'Parsed_Length'
    if 'Delivery' in SOURCE1_FIELDS:
        mappings['Delivery No.'] = 'Delivery'
    
    similar_pairs = [
        ('customer', 'cutomer', 'soldto', 'shipto', 'sold-to'),
        ('no.', 'no', 'number', 'salesdocument', 'delivery', 'deliverynumber'),
        ('kg', 'weight', 'netweight', 'stockweight', 'metalweight'),
        ('pc', 'quantity', 'shippedquantity', 'billedquantity'),
        ('date', 'pricingdate', 'billingdate', 'goodissuedate', 'goods mvtdate'),
        ('total', 'netvalue', 'grossvalue'),
        ('unitprice',),
        ('invoice', 'bill.doc.'),
        ('sales', 'salesord.'),
        ('market', 'country'),
        ('drawing',),
        ('cimalex', 'batch'),
        ('metalprice', 'metal'),
        ('av',),
        ('美金汇率', 'exchangerate', 'salesexchangerate')
    ]
    
    for target in TARGET_COLUMNS:
        if target in mappings:
            continue
        target_norm = normalize_string(target)
        for source in source_fields:
            source_norm = normalize_string(source)
            if target_norm == source_norm:
                mappings[target] = source
                break
            for pair in similar_pairs:
                if any(normalize_string(p) in target_norm for p in pair) and \
                   any(normalize_string(p) in source_norm for p in pair):
                    if target not in mappings:
                        mappings[target] = source

    # Keep user-saved mappings, but fill any missing fields with the current
    # auto-detected defaults so newer fields do not disappear when an older
    # saved mapping file is present.
    if saved:
        merged = mappings.copy()
        if 'Cimalex' in saved:
            merged['Cimalex'] = saved.get('Cimalex', '')
        for key, value in saved.items():
            if key == 'Cimalex':
                continue
            if value not in [None, '']:
                merged[key] = value
        if 'Shipped Quantity BUOM' in SOURCE1_FIELDS:
            merged['kg'] = 'Shipped Quantity BUOM'
        if 'Shipped Quantity' in SOURCE1_FIELDS:
            merged['PC'] = 'Shipped Quantity'
        return merged

    return mappings

@app.route('/')
def index():
    return send_file(INDEX_FILE)

@app.route('/api/upload', methods=['POST'])
def upload_files():
    global SOURCE1_FIELDS, SOURCE2_FIELDS, source1_df, source2_df
    
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({'error': 'Please upload both files.'}), 400
    
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    source1_df = pd.read_excel(file1)
    source2_df = pd.read_excel(file2)

    error_response = require_columns(source1_df, ['Sales Document'], '源文件 1')
    if error_response:
        return error_response
    error_response = require_columns(source2_df, ['Bill. Doc.', 'BillT'], '源文件 2')
    if error_response:
        return error_response
    
    source1_df = source1_df[source1_df['Sales Document'].notna()].reset_index(drop=True)
    
    source1_df = summarize_source1_by_delivery(source1_df)
    
    source2_df = source2_df[~source2_df['Bill. Doc.'].astype(str).str.startswith('PBD', na=False)].reset_index(drop=True)
    
    source2_df = source2_df[source2_df['BillT'] != 'ZPRI'].reset_index(drop=True)
    
    # Split Material Description into helper columns for mapping.
    if 'Material Description' in source1_df.columns:
        source1_df[['Parsed_Product', 'Parsed_Drawing', 'Parsed_Spec', 'Parsed_Alloy', 'Parsed_ItemCat', 'Parsed_Length']] = \
            source1_df['Material Description'].apply(split_material_description)
    
    SOURCE1_FIELDS = list(source1_df.columns)
    SOURCE2_FIELDS = list(source2_df.columns)
    
    mappings = auto_map_fields()
    has_saved_mappings = os.path.exists(MAPPINGS_FILE) and load_saved_mappings()
    
    return jsonify({
        'source1_fields': SOURCE1_FIELDS,
        'source2_fields': SOURCE2_FIELDS,
        'target_fields': TARGET_COLUMNS,
        'auto_mappings': mappings,
        'source1_count': len(source1_df),
        'source2_count': len(source2_df),
        'has_saved_mappings': has_saved_mappings
    })

@app.route('/api/save_mappings', methods=['POST'])
def save_mappings():
    mappings = request.json.get('mappings', {})
    save_mappings_to_file(mappings)
    return jsonify({'success': True, 'message': 'Mappings saved.'})

@app.route('/api/reset_mappings', methods=['POST'])
def reset_mappings():
    if os.path.exists(MAPPINGS_FILE):
        os.remove(MAPPINGS_FILE)
    return jsonify({'success': True, 'message': 'Mappings reset.'})

@app.route('/api/debug_match', methods=['GET'])
def debug_match():
    global source1_df, source2_df
    delivery = request.args.get('delivery', '')
    delivery_num = pd.to_numeric(pd.Series([delivery]), errors='coerce').iloc[0]
    result = {
        'delivery': delivery,
        'source1_count': 0,
        'source2_count': 0,
        'source1_rows': [],
        'source2_rows': [],
    }
    if source1_df is not None and 'Delivery' in source1_df.columns:
        s1_num = pd.to_numeric(source1_df['Delivery'], errors='coerce')
        s1 = source1_df[s1_num == delivery_num]
        result['source1_count'] = len(s1)
        result['source1_rows'] = serialize_dataframe_rows(s1)
    if source2_df is not None and 'Delivery number' in source2_df.columns:
        s2_num = pd.to_numeric(source2_df['Delivery number'], errors='coerce')
        s2 = source2_df[s2_num == delivery_num]
        result['source2_count'] = len(s2)
        result['source2_rows'] = serialize_dataframe_rows(s2)
    return jsonify(result)

@app.route('/api/preview', methods=['POST'])
def preview_data():
    global source1_df, source2_df
    if source1_df is None or source2_df is None:
        return jsonify({'error': '璇峰厛涓婁紶鏂囦欢'}), 400
    
    mappings = request.json.get('mappings', {})
    
    result_df = pd.DataFrame(columns=TARGET_COLUMNS)
    preview_rows = []
    
    for idx, row in source1_df.iterrows():
        delivery = row.get('Delivery', '')
        
        source2_rows = [None]
        has_source2_match = False
        if pd.notna(delivery) and 'Delivery number' in source2_df.columns:
            match_rows = source2_df[source2_df['Delivery number'] == delivery]
            if not match_rows.empty:
                source2_rows = [match_rows.iloc[i] for i in range(len(match_rows))]
                has_source2_match = True
        if str(delivery).startswith('15700006'):
            print(f'[DEBUG preview] delivery={delivery} source2_matches={len(source2_rows) if has_source2_match else 0}')
            if has_source2_match:
                print('[DEBUG preview] matched source2 delivery numbers:', [r.get('Delivery number') for r in source2_rows])
        
        for source2_row in source2_rows:
            new_row = build_report_row(row, source2_row, mappings, source1_df, source2_df, idx, has_source2_match)
            preview_rows.append({
                **new_row,
                '_delivery_matched': has_source2_match,
                '_delivery_match_label': '' if has_source2_match else '未匹配 Delivery number',
            })
            result_df = pd.concat([result_df, pd.DataFrame([new_row])], ignore_index=True)
    
    return jsonify({
        'preview_data': preview_rows,
        'total_count': len(result_df)
    })

@app.route('/api/generate', methods=['POST'])
def generate_report():
    global source1_df, source2_df
    if source1_df is None:
        return jsonify({'error': '璇峰厛涓婁紶鏂囦欢'}), 400
    
    mappings = request.json.get('mappings', {})
    sheet_name = request.json.get('sheet_name', 'ZRL')
    result_df = pd.DataFrame(columns=TARGET_COLUMNS)
    
    for idx, row in source1_df.iterrows():
        delivery = row.get('Delivery', '')
        
        source2_rows = [None]
        has_source2_match = False
        if pd.notna(delivery) and 'Delivery number' in source2_df.columns:
            match_rows = source2_df[source2_df['Delivery number'] == delivery]
            if not match_rows.empty:
                source2_rows = [match_rows.iloc[i] for i in range(len(match_rows))]
                has_source2_match = True
        if str(delivery).startswith('15700006'):
            print(f'[DEBUG generate] delivery={delivery} source2_matches={len(source2_rows) if has_source2_match else 0}')
            if has_source2_match:
                print('[DEBUG generate] matched source2 delivery numbers:', [r.get('Delivery number') for r in source2_rows])
        
        for source2_row in source2_rows:
            new_row = build_report_row(row, source2_row, mappings, source1_df, source2_df, idx, has_source2_match)
            result_df = pd.concat([result_df, pd.DataFrame([new_row])], ignore_index=True)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        result_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        text_format = '@'
        
        target_text_columns = ['Item Cat', 'Ship To', 'Delivery No.']
        other_text_columns = ['Cutomer', 'Sales Document Item', 'Sold To']
        target_number_columns = ['Net Total', 'Tax Amount', 'kg', 'PC', 'Metal', 'Weight/PC', 'Total']
        
        for col_name in target_text_columns + other_text_columns:
            if col_name in result_df.columns:
                col_idx = result_df.columns.get_loc(col_name) + 1
                for row in range(2, len(result_df) + 2):
                    cell = worksheet.cell(row=row, column=col_idx)
                    cell.number_format = text_format

        number_format = '#,##0.00'
        for col_name in target_number_columns:
            if col_name in result_df.columns:
                col_idx = result_df.columns.get_loc(col_name) + 1
                for row in range(2, len(result_df) + 2):
                    cell = worksheet.cell(row=row, column=col_idx)
                    cell.number_format = number_format
    
    output.seek(0)
    filename = f'sales_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    print('Starting Excel report generator...')
    print('Please open in browser: http://localhost:5000')
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host=host, port=port, debug=debug)

