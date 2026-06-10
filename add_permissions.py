from app.models.db import get_connection

with get_connection() as conn:
    admin_role_id = 1
    
    features = [8, 9, 10]
    
    for feature_id in features:
        conn.execute('''
            INSERT OR IGNORE INTO role_permissions (role_id, feature_id)
            VALUES (?, ?)
        ''', (admin_role_id, feature_id))
    
    conn.commit()
    print('已为超级管理员添加瞭望管理子菜单权限！')
    
    rows = conn.execute('''
        SELECT rp.feature_id, f.name 
        FROM role_permissions rp 
        JOIN features f ON rp.feature_id = f.id 
        WHERE rp.role_id = 1
        ORDER BY rp.feature_id
    ''').fetchall()
    print('超级管理员拥有的权限:')
    for row in rows:
        print(f"ID:{row['feature_id']}, 名称:{row['name']}")
