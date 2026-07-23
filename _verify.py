import re, subprocess, os, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(BASE, 'docs', 'index.html'), encoding='utf-8').read()

# 1) 用 Python re 复刻 JS 正则，实测 admonition 转换逻辑
rx = re.compile(r'^:::\s*(tip|info|warning|danger|success|details)\b\s*(.*)$([\s\S]*?)^:::\s*$', re.M)

def prerender(text):
    def repl(m):
        t = m.group(2).strip()
        if m.group(1) == 'details':
            return '\n<details class="admonition details"><summary class="admonition-title">' + (t or '详情') + '</summary>\n' + m.group(3).strip() + '\n</details>\n'
        title_html = ('<p class="admonition-title">' + t + '</p>') if t else ''
        return '\n<div class="admonition ' + m.group(1) + '">' + title_html + '\n' + m.group(3).strip() + '\n</div>\n'
    return rx.sub(repl, text)

samples = [
    '普通段落，没有 ::: 不应被改动。\n\n- [ ] 任务\n- [x] 完成',
    '::: tip 小提示\n这是一段**提示**内容，含 `code`。\n:::',
    '::: warning\n没有标题的警告框\n:::',
    '::: details 点击展开\n隐藏的详细内容\n:::',
    '代码块里出现 ::: 不应被误伤：\n```\n::: not a block\n```',
]
print('=== admonition 转换实测 ===')
for i, s in enumerate(samples):
    print('--- 样例', i, '---')
    out = prerender(s)
    print(out)
    # 断言：普通文本与代码块内的 ::: 不被改动
    if i == 0 and (':::' in out):
        print('!! 错误：普通文本被改动')
    if i == 4 and ('::: not a block' not in out):
        print('!! 错误：代码块内 ::: 被误伤')

# 2) 检查关键特性字符串存在
print('=== 关键特性检查 ===')
for key in ['admonition', 'card-grid', '.card', 'markdown:{', 'prerender', 'kbd', 'text-rendering', '::: details', 'thead th']:
    print(('✓' if key in html else '✗'), key)

# 3) 启动本地服务并检查 200
import http.server, socketserver, threading
os.chdir(os.path.join(BASE, 'docs'))
handler = http.server.SimpleHTTPRequestHandler
httpd = socketserver.TCPServer(('127.0.0.1', 8097), handler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
try:
    with urllib.request.urlopen('http://127.0.0.1:8097/index.html', timeout=5) as r:
        print('本地服务 index.html:', r.status)
    # README 卡片
    with urllib.request.urlopen('http://127.0.0.1:8097/README.md', timeout=5) as r:
        rd = r.read().decode('utf-8')
        print('README 含 card-grid:', 'card-grid' in rd, '| 含 card:', rd.count('class="card"'))
finally:
    httpd.shutdown()
print('DONE')
