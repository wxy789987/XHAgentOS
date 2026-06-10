from app.models.db import get_connection

with get_connection() as conn:
    cursor = conn.execute("PRAGMA table_info(features)")
    columns = cursor.fetchall()
    print("features 表结构:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
    
    print("\n现有的功能列表:")
    rows = conn.execute('SELECT * FROM features').fetchall()
    for row in rows:
        print(f"ID:{row['id']}, 名称:{row['name']}")
