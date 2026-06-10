import requests
import json

s = requests.Session()
s.get('http://localhost:10086/auth/login')
xsrf = s.cookies.get('_xsrf', '')
s.post('http://localhost:10086/auth/login', data={'username': 'admin', 'password': 'admin123', '_xsrf': xsrf}, allow_redirects=False)

r = s.get('http://localhost:10086/admin/feature/menu')
menus = r.json()

for menu in menus:
    print(f"菜单: {menu['name']}")
    children = menu.get('children', [])
    print(f"  子菜单类型: {type(children)}")
    print(f"  子菜单数量: {len(children) if isinstance(children, list) else 'N/A'}")
    if isinstance(children, list):
        for child in children:
            print(f"    - {child['name']}")
    else:
        print(f"    子菜单内容: {children[:100] if children else '空'}")
    print()
