from app.models.db import get_connection

with get_connection() as conn:
    conn.execute('''
        UPDATE features 
        SET url = NULL 
        WHERE id = 7
    ''')
    conn.commit()
    print('已修复瞭望管理菜单，移除了父菜单的URL')
    
    rows = conn.execute('SELECT id, name, url, parent_id FROM features WHERE id=7 OR parent_id=7').fetchall()
    print('\\n修复后的菜单结构:')
    for row in rows:
        indent = '  ' if row['parent_id'] == 7 else ''
        print(f"{indent}ID:{row['id']}, 名称:{row['name']}, URL:{row['url']}")
