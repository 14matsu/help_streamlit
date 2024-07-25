import streamlit as st
import pandas as pd
from datetime import datetime
import io
import base64
import asyncio
from database import init_db, get_shifts, save_shift, save_store_help_request, get_store_help_requests
from pdf_generator import generate_pdf,generate_help_table_pdf,generate_individual_pdf
from constants import EMPLOYEES, SHIFT_TYPES, STORE_COLORS, WEEKDAY_JA,AREAS
from utils import parse_shift, format_shifts, update_session_state_shifts, highlight_weekend, get_store_index, get_shift_type_index, is_shift_filled, highlight_filled_shifts

@st.cache_data(ttl=3600)
def get_cached_shifts(year, month):
    start_date = pd.Timestamp(year, month, 16)
    end_date = start_date + pd.DateOffset(months=1) - pd.Timedelta(days=1)
    return get_shifts(start_date, end_date)

async def save_shift_async(date, employee, shift_str):
    await asyncio.to_thread(save_shift, date, employee, shift_str)
    
    current_month = date.replace(day=1)
    previous_month = current_month - pd.DateOffset(months=1)
    get_cached_shifts.clear()
    get_cached_shifts(current_month.year, current_month.month)
    get_cached_shifts(previous_month.year, previous_month.month)
    
    st.experimental_rerun()

def initialize_shift_data(year, month):
    if 'shift_data' not in st.session_state or st.session_state.current_year != year or st.session_state.current_month != month:
        start_date = pd.Timestamp(year, month, 16)
        end_date = start_date + pd.DateOffset(months=1) - pd.Timedelta(days=1)
        date_range = pd.date_range(start=start_date, end=end_date)
        st.session_state.shift_data = pd.DataFrame(
            index=date_range,
            columns=EMPLOYEES,
            data='-'
        )
        st.session_state.current_year = year
        st.session_state.current_month = month

def display_shift_table(selected_year, selected_month):
    st.header('ヘルプ表')
    
    if not isinstance(st.session_state.shift_data.index, pd.DatetimeIndex):
        st.session_state.shift_data.index = pd.to_datetime(st.session_state.shift_data.index)
    
    start_date = pd.Timestamp(selected_year, selected_month, 16)
    end_date = start_date + pd.DateOffset(months=1) - pd.Timedelta(days=1)
    
    display_data = st.session_state.shift_data[
        (st.session_state.shift_data.index >= start_date) & 
        (st.session_state.shift_data.index <= end_date)
    ].copy()   

    items_per_page = 15
    total_pages = len(display_data) // items_per_page + (1 if len(display_data) % items_per_page > 0 else 0)
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    # ページナビゲーション
    col1, col2, col3 = st.columns([2,3,2])
    with col1:
        if st.button('◀◀ 最初', key='first_page'):
            st.session_state.current_page = 1
            st.experimental_rerun()
        if st.button('◀ 前へ', key='prev_page') and st.session_state.current_page > 1:
            st.session_state.current_page -= 1
            st.experimental_rerun()
    with col2:
        st.write(f'ページ {st.session_state.current_page} / {total_pages}')
    with col3:
        if st.button('最後 ▶▶', key='last_page'):
            st.session_state.current_page = total_pages
            st.experimental_rerun()

        if st.button('次へ ▶', key='next_page') and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
            st.experimental_rerun()

    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page

    display_data = display_data.iloc[start_idx:end_idx]

    display_data['日付'] = display_data.index.strftime('%Y-%m-%d')
    display_data['曜日'] = display_data.index.strftime('%a').map(WEEKDAY_JA)
    display_data = display_data.reset_index(drop=True)
    display_data = display_data[['日付', '曜日'] + EMPLOYEES]
    display_data = display_data.fillna('-')

    # CSSでテーブルのスタイルを調整
    st.markdown("""
    <style>
    table {
        font-size: 16px;
        width: 100%;
    }
    th, td {
        text-align: center;
        padding: 10px;
        white-space: pre-line;
        vertical-align: top;
    }
    th {
        background-color: #f0f0f0;
    }
    </style>
    """, unsafe_allow_html=True)

    # スタイリングを適用
    styled_df = display_data.style.format(format_shifts, subset=EMPLOYEES)\
                               .apply(highlight_weekend, axis=1)
    
    st.write(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # PDFダウンロードボタンを追加
    pdf = generate_help_table_pdf(display_data.reset_index(), selected_year, selected_month)
    st.download_button(
        label="ヘルプ表をPDFでダウンロード",
        data=pdf,
        file_name=f"help_table_{selected_year}_{selected_month}.pdf",
        mime="application/pdf"
    )

def update_shift_input(current_shift):
    shift_type, times, stores = parse_shift(current_shift)
    new_shift_type = st.selectbox('種類', ['AM可', 'PM可', '1日可', '-'], index=['AM可', 'PM可', '1日可', '-'].index(shift_type) if shift_type in ['AM可', 'PM可', '1日可'] else 3)
    
    if new_shift_type in ['AM可', 'PM可', '1日可']:
        num_shifts = st.number_input('シフト数', min_value=1, max_value=5, value=len(times) or 1)
        
        new_times = []
        new_stores = []
        for i in range(num_shifts):
            col1, col2, col3 = st.columns(3)
            with col1:
                area = st.selectbox(f'エリア {i+1}', list(AREAS.keys()), key=f'shift_area_{i}')
                
            with col2:
                store_options = [''] + AREAS[area] if area != 'なし' else ['']
                store = st.selectbox(f'店舗 {i+1}', store_options, index=store_options.index(stores[i]) if i < len(stores) and stores[i] in store_options else 0, key=f'shift_store_{i}')
            with col3:
                time = st.text_input(f'時間 {i+1}', value=times[i] if i < len(times) else '')
            if time:
                new_times.append(time)
                new_stores.append(store)
        
        if new_times:
            new_shift_str = f"{new_shift_type},{','.join([f'{t}@{s}' if s else t for t, s in zip(new_times, new_stores)])}"
        else:
            new_shift_str = new_shift_type
    
    elif new_shift_type == '-':
        new_shift_str = '-'
    
    return new_shift_str

def display_store_help_requests(selected_year, selected_month):
    st.header('店舗ヘルプ希望')
    
    start_date = pd.Timestamp(selected_year, selected_month, 16)
    end_date = start_date + pd.DateOffset(months=1) - pd.Timedelta(days=1)
    
    store_help_requests = get_store_help_requests(start_date, end_date)
    
    if store_help_requests.empty:
        st.write("ヘルプ希望はありません。")
    else:
        store_help_requests['日付'] = store_help_requests.index.strftime('%Y-%m-%d')
        store_help_requests['曜日'] = store_help_requests.index.strftime('%a').map(WEEKDAY_JA)
        
        # 存在しない店舗列を追加
        all_stores = [store for stores in AREAS.values() for store in stores]
        for store in all_stores:
            if store not in store_help_requests.columns:
                store_help_requests[store] = '-'
        
        store_help_requests = store_help_requests.reset_index(drop=True)

        # エリアごとにタブを作成（「なし」を除外）
        area_tabs = [area for area in AREAS.keys() if area != 'なし']
        tabs = st.tabs(area_tabs)
        
        # CSSでテーブルのスタイルを調整
        st.markdown("""
        <style>
        table {
            font-size: 14px;
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            text-align: center;
            padding: 8px;
            border: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for area, tab in zip(area_tabs, tabs):
            with tab:
                area_stores = AREAS[area]
                area_data = store_help_requests[['日付', '曜日'] + area_stores]
                area_data = area_data.fillna('-')

                # シフトデータを取得し、インデックスをDateTime型に変換
                shift_data = st.session_state.shift_data[
                    (st.session_state.shift_data.index >= start_date) & 
                    (st.session_state.shift_data.index <= end_date)
                ]
                shift_data.index = pd.to_datetime(shift_data.index)

                # スタイリングを適用
                styled_df = area_data.style.apply(highlight_weekend, axis=1)\
                                           .apply(highlight_filled_shifts, shift_data=shift_data, axis=1)

                st.write(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        # CSVダウンロードボタンを追加
        csv = store_help_requests.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="店舗ヘルプ希望をCSVでダウンロード",
            data=csv,
            file_name=f"store_help_requests_{selected_year}_{selected_month}.csv",
            mime="text/csv",
        )
async def main():
    st.set_page_config(layout="wide")
    st.title('ヘルプ管理アプリ')

    with st.sidebar:
        st.header('設定')
        current_year = datetime.now().year
        selected_year = st.selectbox('年を選択', range(current_year , current_year + 10), key='year_selector')
        selected_month = st.selectbox('月を選択', range(1, 13), key='month_selector')

        initialize_shift_data(selected_year, selected_month)

        shifts = get_cached_shifts(selected_year, selected_month)
        update_session_state_shifts(shifts)

        st.header('シフト登録/修正')
        
        employee = st.selectbox('従業員を選択', EMPLOYEES)
        start_date = datetime(selected_year, selected_month, 16)
        end_date = start_date + pd.DateOffset(months=1) - pd.Timedelta(days=1)

        # デフォルト値を範囲内に設定
        default_date = max(min(datetime.now().date(), end_date.date()), start_date.date())
        
        date = st.date_input('日付を選択', min_value=start_date.date(), max_value=end_date.date(), value=default_date)
        
        if not isinstance(st.session_state.shift_data.index, pd.DatetimeIndex):
            st.session_state.shift_data.index = pd.to_datetime(st.session_state.shift_data.index)

        date = pd.Timestamp(date)

        if date in st.session_state.shift_data.index:
            current_shift = st.session_state.shift_data.loc[date, employee]
            if pd.isna(current_shift) or isinstance(current_shift, (int, float)):
                current_shift = '休み'
        else:
            current_shift = '休み'
        
        new_shift_str = update_shift_input(current_shift)

        if st.button('保存'):
            await save_shift_async(date, employee, new_shift_str)
            st.session_state.shift_data.loc[date, employee] = new_shift_str
            st.success('保存しました')
            st.experimental_rerun()

        st.header('店舗ヘルプ希望登録')
        area = st.selectbox('エリアを選択', [key for key in AREAS.keys() if key != 'なし'], key='help_area')
        store = st.selectbox('店舗を選択', AREAS[area], key='help_store')
        help_default_date = max(min(datetime.now().date(), end_date.date()), start_date.date())
        
        help_date = st.date_input('日付を選択', min_value=start_date.date(), max_value=end_date.date(), value=help_default_date, key='help_date')
        help_time = st.text_input('時間帯')
        if st.button('ヘルプ希望を登録'):
            save_store_help_request(help_date, store, help_time)
            st.success('ヘルプ希望を登録しました')
            st.experimental_rerun()

        st.header('個別PDFのダウンロード')
        selected_employee = st.selectbox('従業員を選択', EMPLOYEES, key='pdf_employee_selector')
        if st.button('PDFを生成'):
            employee_data = st.session_state.shift_data[selected_employee]
            pdf_buffer = generate_individual_pdf(employee_data, selected_employee, selected_year, selected_month)
            start_date = pd.Timestamp(selected_year, selected_month, 16)
            end_date = start_date + pd.DateOffset(months=1) - pd.Timedelta(days=1)
            file_name = f'{selected_employee}さん_{start_date.strftime("%Y年%m月%d日")}～{end_date.strftime("%Y年%m月%d日")}_シフト.pdf'
            st.download_button(
                label=f"{selected_employee}さんのPDFをダウンロード",
                data=pdf_buffer.getvalue(),
                file_name=file_name,
                mime="application/pdf"
            )

        if st.button('CSVとしてエクスポート'):
            csv_buffer = io.StringIO()
            st.session_state.shift_data.to_csv(csv_buffer, index=True)
            st.download_button(
                label="CSVをダウンロード",
                data=csv_buffer.getvalue(),
                file_name="shift_data.csv",
                mime="text/csv"
            )

    display_shift_table(selected_year, selected_month)
    display_store_help_requests(selected_year, selected_month)

if __name__ == '__main__':
    init_db()
    asyncio.run(main())