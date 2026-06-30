import pandas as pd


from app import build_month_end_report_df


def test_month_end_report_uses_b_as_base_and_enriches_from_a_and_c():
    source_a_df = pd.DataFrame([
        {
            'Delivery': 15700030,
            'Material': '86176669',
            'Item Description': 'FMPE_TES9001_MPC_1729.2MM_3003_H112',
        },
        {
            'Delivery': 15700031,
            'Material': '86176670',
            'Item Description': 'FMPE_TES9002_MPC_1800MM_3003_H112',
        },
    ])
    source_b_df = pd.DataFrame([
        {
            'SD Document': 15700030,
            'Sales Organization': 1471,
            'Billing Date': '2026-06-02',
            'Net Value': 23545.0,
        },
        {
            'SD Document': 15700032,
            'Sales Organization': 1472,
            'Billing Date': '2026-06-03',
            'Net Value': 999.0,
        },
    ])
    source_c_df = pd.DataFrame([
        {
            'Material': '86176669',
            'Plant': 1471,
            'Profit Center': '14701100',
        },
        {
            'Material': '86176670',
            'Plant': 1471,
            'Profit Center': '14701101',
        },
    ])

    result_df = build_month_end_report_df(source_a_df, source_b_df, source_c_df)

    assert list(result_df['SD Document']) == [15700030, 15700032]
    assert result_df.loc[0, 'Material'] == '86176669'
    assert result_df.loc[0, 'Item Description'] == 'FMPE_TES9001_MPC_1729.2MM_3003_H112'
    assert result_df.loc[0, 'Profit Center'] == '14701100'
    assert result_df.loc[1, 'Material'] == ''
    assert result_df.loc[1, 'Item Description'] == ''
    assert result_df.loc[1, 'Profit Center'] == ''


def test_month_end_report_leaves_missing_matches_blank():
    source_a_df = pd.DataFrame(columns=['Delivery', 'Material', 'Item Description'])
    source_b_df = pd.DataFrame([
        {
            'SD Document': 99999999,
            'Sales Organization': 1471,
            'Billing Date': '2026-06-02',
            'Net Value': 100.0,
        }
    ])
    source_c_df = pd.DataFrame(columns=['Material', 'Plant', 'Profit Center'])

    result_df = build_month_end_report_df(source_a_df, source_b_df, source_c_df)

    assert result_df.loc[0, 'Material'] == ''
    assert result_df.loc[0, 'Item Description'] == ''
    assert result_df.loc[0, 'Profit Center'] == ''
