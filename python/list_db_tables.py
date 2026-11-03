import pyodbc

SERVER = r"LEGACY\LEGACY"
DATABASE = "Sigma_Cap"
DRIVER = "{ODBC Driver 17 for SQL Server}"

CONN_STR = f"Driver={DRIVER};Server={SERVER};Database={DATABASE};Trusted_Connection=yes;"

try:
    conn = pyodbc.connect(CONN_STR)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TABLE_NAME, TABLE_TYPE 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'dbo'
        ORDER BY TABLE_TYPE, TABLE_NAME;
    """)
    tables = cursor.fetchall()
    print("Found items in Sigma_Cap database:")
    for t in tables:
        print(f"- {t[0]} ({t[1]})")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
