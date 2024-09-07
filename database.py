import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
import pandas as pd
from constants import AREAS

# データベース接続情報（環境変数から取得）
DB_NAME = os.environ.get("POSTGRES_DB", "helpshift_db")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "0992989324")
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # shiftsテーブルを作成（存在しない場合）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS shifts (
        date DATE,
        employee TEXT,
        shift TEXT,
        PRIMARY KEY (date, employee)
    )
    """)
    
    # store_help_requestsテーブルを作成（存在しない場合）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS store_help_requests (
        date DATE,
        store TEXT,
        help_time TEXT,
        PRIMARY KEY (date, store)
    )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def get_shifts(start_date, end_date):
    conn = get_db_connection()
    query = """
    SELECT date, employee, shift
    FROM shifts
    WHERE date BETWEEN %s AND %s
    """
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()
    
    df['date'] = pd.to_datetime(df['date'])
    return df.pivot(index='date', columns='employee', values='shift')

def save_shift(date, employee, shift_str):
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
    INSERT INTO shifts (date, employee, shift)
    VALUES (%s, %s, %s)
    ON CONFLICT (date, employee) DO UPDATE
    SET shift = EXCLUDED.shift
    """
    cur.execute(query, (date, employee, shift_str))
    conn.commit()
    cur.close()
    conn.close()

def save_store_help_request(date, store, help_time):
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
    INSERT INTO store_help_requests (date, store, help_time)
    VALUES (%s, %s, %s)
    ON CONFLICT (date, store) DO UPDATE
    SET help_time = EXCLUDED.help_time
    """
    cur.execute(query, (date, store, help_time))
    conn.commit()
    cur.close()
    conn.close()

def get_store_help_requests(start_date, end_date):
    conn = get_db_connection()
    query = """
    SELECT date, store, help_time
    FROM store_help_requests
    WHERE date BETWEEN %s AND %s
    """
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
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