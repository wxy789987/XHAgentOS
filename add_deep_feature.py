from app.models.db import get_connection

with get_connection() as conn:
    conn.execute('''
        INSERT OR IGNORE INTO features 
        (id, name, code, icon, parent_id, url, sort, is_active, create_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (10, 'AI深度采集', 'lookout_deep', 'layui-icon-search', 7, '/admin/lookout/deep', 3, 1))
    
    conn.execute('''
        INSERT OR IGNORE INTO features 
        (id, name, code, icon, parent_id, url, sort, is_active, create_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (8, '瞭望采集', 'lookout_collect', 'layui-icon-collect', 7, '/admin/lookout/collect', 1, 1))
    
    conn.execute('''
        INSERT OR IGNORE INTO features 
        (id, name, code, icon, parent_id, url, sort, is_active, create_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (9, '数据仓库', 'lookout_warehouse', 'layui-icon-folder', 7, '/admin/lookout/warehouse', 2, 1))
    
    conn.commit()
    print('已添加瞭望管理子菜单！')
    
    rows = conn.execute('SELECT id, name, parent_id, url FROM features WHERE parent_id=7').fetchall()
    print('瞭望管理子菜单:')
    for row in rows:
        print(f"ID:{row['id']}, 名称:{row['name']}, URL:{row['url']}")
