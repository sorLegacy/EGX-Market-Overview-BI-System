import pyodbc

SERVER = r"LEGACY\LEGACY"
DATABASE = "Sigma_Cap"
DRIVER = "{ODBC Driver 17 for SQL Server}"

CONN_STR = f"Driver={DRIVER};Server={SERVER};Database={DATABASE};Trusted_Connection=yes;"

try:
    conn = pyodbc.connect(CONN_STR)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            TABLE_NAME, 
            COLUMN_NAME, 
            DATA_TYPE, 
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
        ORDER BY TABLE_NAME, ORDINAL_POSITION;
    """)
    rows = cursor.fetchall()
    
    current_table = None
    for r in rows:
        tbl, col, dtype, char_len, num_prec, num_scale = r
        if tbl != current_table:
            current_table = tbl
            print(f"\n### Table / View: {current_table}")
        if dtype in ('decimal', 'numeric'):
            print(f"  - {col}: {dtype}({num_prec},{num_scale})")
        elif dtype in ('nvarchar', 'varchar'):
            print(f"  - {col}: {dtype}({char_len})")
        else:
            print(f"  - {col}: {dtype}")
            
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error querying database: {e}")
