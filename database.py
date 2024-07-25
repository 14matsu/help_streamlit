import sqlite3
import pandas as pd
from constants import AREAS

DB_NAME = 'shifts.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS shifts
        (date TEXT, employee TEXT, shift TEXT, PRIMARY KEY (date, employee))
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS store_help_requests
        (date TEXT, store TEXT, help_time TEXT, PRIMARY KEY (date, store))
    ''')
    conn.commit()
    conn.close()

def get_shifts(start_date, end_date):
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT date, employee, shift
    FROM shifts
    WHERE date BETWEEN ? AND ?
    """
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    df = pd.read_sql_query(query, conn, params=(start_date_str, end_date_str))
    conn.close()
    
    df['date'] = pd.to_datetime(df['date'])
    
    return df.pivot(index='date', columns='employee', values='shift')

def save_shift(date, employee, shift_str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    date_str = date.strftime('%Y-%m-%d')
    
    query = """
    INSERT OR REPLACE INTO shifts (date, employee, shift)
    VALUES (?, ?, ?)
    """
    cursor.execute(query, (date_str, employee, shift_str))
    
    conn.commit()
    conn.close()

def save_store_help_request(date, store, help_time):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    date_str = date.strftime('%Y-%m-%d')
    
    query = """
    INSERT OR REPLACE INTO store_help_requests (date, store, help_time)
    VALUES (?, ?, ?)
    """
    cursor.execute(query, (date_str, store, help_time))
    
    conn.commit()
    conn.close()

def get_store_help_requests(start_date, end_date):
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT date, store, help_time
    FROM store_help_requests
    WHERE date BETWEEN ? AND ?
    """
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    df = pd.read_sql_query(query, conn, params=(start_date_str, end_date_str))
    conn.close()
    
    df['date'] = pd.to_datetime(df['date'])
    
    # ピボットテーブルを作成し、欠損値を'-'で埋める
    pivot_df = df.pivot(index='date', columns='store', values='help_time').fillna('-')
    
    # 全ての店舗列が存在することを確認
    all_stores = [store for stores in AREAS.values() for store in stores]
    for store in all_stores:
        if store not in pivot_df.columns:
            pivot_df[store] = '-'
    
    return pivot_df
