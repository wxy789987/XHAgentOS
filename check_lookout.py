from app.models.db import get_connection

with get_connection() as conn:
    print("=== 检查瞭望管理菜单 ===")
    row = conn.execute('SELECT * FROM features WHERE id=7').fetchone()
    if row:
        print(f"瞭望管理存在: ID={row['id']}, 名称={row['name']}, URL={row['url']}, is_active={row['is_active']}")
    else:
        print("❌ 瞭望管理不存在！")
    
    print("\n=== 瞭望管理子菜单 ===")
    rows = conn.execute('SELECT * FROM features WHERE parent_id=7 ORDER BY sort').fetchall()
    if rows:
        for row in rows:
            print(f"ID={row['id']}, 名称={row['name']}, URL={row['url']}, sort={row['sort']}")
    else:
        print("❌ 没有子菜单！")
