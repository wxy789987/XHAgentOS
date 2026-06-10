from app.models.db import get_connection

with get_connection() as conn:
    conn.execute('UPDATE features SET url = NULL WHERE id = 7')
    conn.commit()
    row = conn.execute('SELECT id, name, url FROM features WHERE id=7').fetchone()
    print(f"修复完成: ID={row['id']}, 名称={row['name']}, URL={row['url']}")
