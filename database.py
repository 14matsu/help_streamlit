import sqlite3
import pandas as pd
import os
from constants import AREAS

# ローカル環境とStreamlit Cloud環境を区別
if os.environ.get('STREAMLIT_CLOUD'):
    DB_NAME = '/app/data/shifts.db'
else:
    DB_NAME = 'shifts.db'  # ローカルの場合はカレントディレクトリに作成

# データベース初期化時
def init_db():
    if os.environ.get('STREAMLIT_CLOUD'):
        os.makedirs('/app/data', exist_ok=True)
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS shifts
            (date TEXT, employee TEXT, shift TEXT, PRIMARY KEY (date, employee))
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS store_help_requests
            (date TEXT, store TEXT, help_time TEXT, PRIMARY KEY (date, store))
        ''')

def get_shifts(start_date, end_date):
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    with sqlite3.connect(DB_NAME) as conn:
        query = """
        SELECT date, employee, shift
        FROM shifts
        WHERE date BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, conn, params=(start_date_str, end_date_str))
    
    df['date'] = pd.to_datetime(df['date'])
    return df.pivot(index='date', columns='employee', values='shift')

def save_shift(date, employee, shift_str):
    date_str = date.strftime('%Y-%m-%d')
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        query = """
        INSERT OR REPLACE INTO shifts (date, employee, shift)
        VALUES (?, ?, ?)
        """
        cursor.execute(query, (date_str, employee, shift_str))

def save_store_help_request(date, store, help_time):
    date_str = date.strftime('%Y-%m-%d')
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        query = """
        INSERT OR REPLACE INTO store_help_requests (date, store, help_time)
        VALUES (?, ?, ?)
        """
        cursor.execute(query, (date_str, store, help_time))

def get_store_help_requests(start_date, end_date):
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    with sqlite3.connect(DB_NAME) as conn:
        query = """
        SELECT date, store, help_time
        FROM store_help_requests
        WHERE date BETWEEN ? AND ?
        """
        df = pd.read_sql_query(query, conn, params=(start_date_str, end_date_str))
    
    df['date'] = pd.to_datetime(df['date'])
    
    # ピボットテーブルを作成し、欠損値を'-'で埋める
    pivot_df = df.pivot(index='date', columns='store', values='help_time').fillna('-')
    
    # 全ての店舗列が存在することを確認
    all_stores = [store for stores in AREAS.values() for store in stores]
    for store in all_stores:
        if store not in pivot_df.columns:
            pivot_df[store] = '-'
    
    return pivot_df