import psycopg2
import os

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
    
    # 既存のテーブルを削除（存在する場合）
    cur.execute("DROP TABLE IF EXISTS shifts")
    cur.execute("DROP TABLE IF EXISTS store_help_requests")
    
    # shiftsテーブルを作成
    cur.execute("""
    CREATE TABLE shifts (
        date DATE,
        employee TEXT,
        shift TEXT,
        PRIMARY KEY (date, employee)
    )
    """)
    
    # store_help_requestsテーブルを作成
    cur.execute("""
    CREATE TABLE store_help_requests (
        date DATE,
        store TEXT,
        help_time TEXT,
        PRIMARY KEY (date, store)
    )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("データベースの初期化が完了しました。")

if __name__ == "__main__":
    init_db()