import requests
import json

s = requests.Session()
s.get('http://localhost:10086/auth/login')
xsrf = s.cookies.get('_xsrf', '')
s.post('http://localhost:10086/auth/login', data={'username': 'admin', 'password': 'admin123', '_xsrf': xsrf}, allow_redirects=False)

r = s.get('http://localhost:10086/admin/feature/menu')
print('菜单API状态:', r.status_code)
if r.status_code == 200:
    menus = r.json()
    print('\n菜单结构:')
    for menu in menus:
        has_children = len(menu.get('children', [])) > 0
        print(f"ID:{menu['id']}, 名称:{menu['name']}, URL:{menu.get('url', '无')}, 子菜单数:{len(menu.get('children', []))}")
        if has_children:
            for child in menu['children']:
                print(f"  └── ID:{child['id']}, 名称:{child['name']}, URL:{child.get('url', '无')}")
