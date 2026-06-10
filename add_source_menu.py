from app.models.db import get_connection

with get_connection() as conn:
    conn.execute('''
        INSERT OR IGNORE INTO features 
        (id, name, code, icon, parent_id, url, sort, is_active, create_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (11, '瞭望源管理', 'lookout_source', 'layui-icon-set', 7, '/admin/lookout/source', 0, 1))
    
    conn.execute('INSERT OR IGNORE INTO role_permissions (role_id, feature_id) VALUES (1, 11)')
    conn.commit()
    print('已添加瞭望源管理子菜单！')
    
    rows = conn.execute('SELECT id, name, url, sort FROM features WHERE parent_id=7 ORDER BY sort').fetchall()
    print('\\n瞭望管理子菜单:')
    for row in rows:
        print(f"ID:{row['id']}, 名称:{row['name']}, URL:{row['url']}, 排序:{row['sort']}")
