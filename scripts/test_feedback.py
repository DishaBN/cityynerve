import requests

s = requests.Session()
city = 'Chikkamagaluru'
print('GET feedback page for', city)
r = s.get(f'http://127.0.0.1:5000/feedback/{city}', timeout=6)
print('GET status', r.status_code)

print('POSTing test feedback...')
data = {
    'traffic':'8',
    'pollution':'6',
    'cost':'4',
    'safety':'7',
    'water':'5',
    'healthcare':'9',
    'heat':'3',
    'responseTime':'6',
    'complaints':'2',
    'feedback_text':'automation test'
}
r = s.post(f'http://127.0.0.1:5000/feedback/{city}', data=data, timeout=6, allow_redirects=True)
print('POST ->', r.status_code, 'URL:', r.url)

print('Fetching admin page to verify')
r2 = s.get('http://127.0.0.1:5000/admin', timeout=6)
print('ADMIN status', r2.status_code)
idx = r2.text.find(city)
print('Found entry:', idx != -1)
if idx != -1:
    start = max(0, idx-200)
    end = idx+200
    print(r2.text[start:end])
else:
    print('City not found in admin page')
