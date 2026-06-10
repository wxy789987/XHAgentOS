from app.models.db import get_connection

with get_connection() as conn:
    print("=== 超级管理员权限 ===")
    rows = conn.execute('''
        SELECT rp.feature_id, f.name, f.url 
        FROM role_permissions rp 
        JOIN features f ON rp.feature_id = f.id 
        WHERE rp.role_id = 1
        ORDER BY rp.feature_id
    ''').fetchall()
    for row in rows:
        print(f"ID={row['feature_id']}, 名称={row['name']}, URL={row['url']}")
    
    print("\n=== 检查瞭望管理权限 ===")
    row = conn.execute('SELECT * FROM role_permissions WHERE role_id=1 AND feature_id=7').fetchone()
    if row:
        print("✅ 超级管理员有瞭望管理权限")
    else:
        print("❌ 超级管理员没有瞭望管理权限！")
