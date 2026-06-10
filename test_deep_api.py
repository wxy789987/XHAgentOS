import requests
import json

s = requests.Session()
s.get('http://localhost:10086/auth/login')
xsrf = s.cookies.get('_xsrf', '')
s.post('http://localhost:10086/auth/login', data={'username': 'admin', 'password': 'admin123', '_xsrf': xsrf}, allow_redirects=False)

print('=== 测试深度采集API ===')

apis = [
    '/admin/lookout/deep/list',
    '/admin/lookout/deep/status',
    '/admin/lookout/deep/analysis',
]

for api in apis:
    r = s.get('http://localhost:10086' + api)
    print(f'{api}: {r.status_code}', end='')
    if r.status_code == 200:
        data = r.json()
        print(f' - code={data.get("code", "N/A")}', end='')
        if 'data' in data:
            if isinstance(data['data'], dict):
                print(f' - keys={list(data["data"].keys())[:5]}')
            elif isinstance(data['data'], list):
                print(f' - count={len(data["data"])}')
            else:
                print()
        else:
            print()
    else:
        print(f' - 错误: {r.text[:100]}')
