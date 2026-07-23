const fs = require('fs');
const vm = require('vm');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, 'docs', 'index.html'), 'utf8');

// 1) 提取内联 <script> 并语法校验（整段配置脚本已包含 prerender 定义）
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
let jsOK = true;
scripts.forEach((s, i) => {
  if (!s.trim()) return;
  try { new vm.Script(s); console.log('Script #' + i + ': OK'); }
  catch (e) { jsOK = false; console.log('Script #' + i + ' ERROR:\n' + e.message); }
});

// 2) 用真实正则实测 admonition 转换（与实际写入一致）
function prerender(text){
  return text.replace(/^:::\s*(tip|info|warning|danger|success|details)\b\s*(.*)$([\s\S]*?)^:::\s*$/gm, function(_, type, title, body){
    var t = title.trim();
    if(type === 'details'){
      return '\n<details class="admonition details"><summary class="admonition-title">'+(t||'详情')+'</summary>\n'+body.trim()+'\n</details>\n';
    }
    var titleHtml = t ? '<p class="admonition-title">'+t+'</p>' : '';
    return '\n<div class="admonition '+type+'">'+titleHtml+'\n'+body.trim()+'\n</div>\n';
  });
}

const samples = [
  '普通段落，没有 ::: 不应被改动。\n\n- [ ] 任务\n- [x] 完成',
  '::: tip 小提示\n这是一段**提示**内容，含 `code`。\n:::',
  '::: warning\n没有标题的警告框\n:::',
  '::: details 点击展开\n隐藏的详细内容\n:::',
  '代码块里出现 ::: 不应被误伤：\n```\n::: not a block\n```'
];
samples.forEach((s, i) => {
  console.log('=== 样例 ' + i + ' ===');
  console.log(prerender(s));
  console.log('');
});

console.log('RESULT:', jsOK ? 'JS 全部通过' : 'JS 存在错误');
