import requests
import json

s = requests.Session()
s.get('http://localhost:10086/auth/login')
xsrf = s.cookies.get('_xsrf', '')
s.post('http://localhost:10086/auth/login', data={'username': 'admin', 'password': 'admin123', '_xsrf': xsrf}, allow_redirects=False)

r = s.get('http://localhost:10086/admin/feature/menu')
menus = r.json()

for menu in menus:
    if menu['name'] == '瞭望管理':
        children = menu.get('children', [])
        print(f"瞭望管理子菜单:")
        for i, child in enumerate(children):
            print(f"  [{i}] 类型: {type(child)}, 值: {child}")
