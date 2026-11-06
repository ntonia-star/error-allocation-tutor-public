'use strict';
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
let view='home',mode='standard',category='全部',level='记忆',calcType='equal',knowledge=[],exercises=[],busy=false;
let history=[];
try{const saved=JSON.parse(localStorage.getItem('error-allocation-chat')||'[]');if(Array.isArray(saved))history=saved.filter(r=>['user','assistant'].includes(r.role)&&typeof r.content==='string').slice(-16);}catch{}
const names={home:'学习首页',chat:'智能问答',knowledge:'课程知识库',calculate:'计算与验算',practice:'考试训练'};
function toast(message){$('#toast').textContent=message;$('#toast').classList.remove('hidden');clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').classList.add('hidden'),5500);}
function navigate(next){if(!names[next])return;view=next;$$('.view').forEach(e=>e.classList.toggle('hidden',e.id!==`view-${next}`));$$('.nav-item').forEach(e=>e.classList.toggle('active',e.dataset.view===next));$('#page-name').textContent=names[next];document.title=`${names[next]} · 误差分配智能教学助手`;if(location.hash!==`#${next}`)window.history.replaceState(null,'',`#${next}`);window.scrollTo({top:0,behavior:'instant'});}
function node(tag,cls,text){const el=document.createElement(tag);if(cls)el.className=cls;if(text!==undefined)el.textContent=text;return el;}
function markdown(target,text){
  const math=[];
  let source=String(text||'').replace(/\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g,(all,display,inline)=>{const i=math.length;math.push({tex:display||inline,display:!!display});return `<span data-math="${i}"></span>`;});
  source=source.replace(/\[S:([\w-]+)\]/g,(_,id)=>{const k=knowledge.find(c=>c.id===id);return k?`〔${k.title}〕`:'〔课程依据〕';});
  target.innerHTML=DOMPurify.sanitize(marked.parse(source,{breaks:true}),{FORBID_TAGS:['img','style','iframe','form','input','button'],FORBID_ATTR:['style']});
  target.querySelectorAll('a').forEach(a=>{if(!a.getAttribute('href')?.startsWith('#')){a.removeAttribute('href');}});
  target.querySelectorAll('[data-math]').forEach(el=>{const m=math[Number(el.dataset.math)];if(m)katex.render(m.tex,el,{displayMode:m.display,throwOnError:false,trust:false,strict:'warn',maxExpand:500});});
}
function sources(target,items){
  if(!items?.length)return;
  const section=node('div','source-section');section.append(node('div','source-caption','课程依据 · 点击查看已核验的原始页面'));
  const links=node('div','source-links');const seen=new Set();
  for(const c of items)for(const s of c.sources||[]){const key=s.url;if(seen.has(key))continue;seen.add(key);const label=s.kind==='教材'?`核验资料 · 印刷 ${s.printed_page} 页 / PDF ${s.pdf_page} 页`:`课件 · PDF ${s.pdf_page} 页 / 幻灯片 ${s.slide}`;const a=node('a','source-link',label);a.href=s.url;a.target='_blank';a.rel='noopener';a.title=`${s.chapter} · ${c.title}`;links.append(a);}
  section.append(links);target.append(section);
}
async function api(path,body){const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),180000);try{const res=await fetch(path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,signal:controller.signal});const data=await res.json();if(!res.ok)throw Error(data.error||'服务暂时不可用');return data;}catch(e){if(e.name==='AbortError')throw Error('本次请求超时，请稍后重试。');if(e instanceof TypeError)throw Error('无法连接服务，请检查网络后重试。');throw e;}finally{clearTimeout(timer);}}
function message(role,text,refs,toolRuns){const box=$('#messages');box.querySelector('.chat-welcome')?.remove();const wrap=node('article',`message ${role}`);wrap.append(node('div','message-label',role==='user'?'你':role==='error'?'服务提示':'误差分配助手'));const content=node('div','message-content');if(role==='user'||role==='error')content.textContent=text;else markdown(content,text);wrap.append(content);if(refs)sources(wrap,refs);if(toolRuns?.length)wrap.append(node('div','tool-note',`✓ 已通过程序计算工具核实 ${toolRuns.length} 个计算步骤`));box.append(wrap);box.scrollTop=box.scrollHeight;return wrap;}
function saveChat(){try{localStorage.setItem('error-allocation-chat',JSON.stringify(history.slice(-16)));}catch{}}
async function sendChat(question){
  question=question.trim();if(!question||busy)return;busy=true;navigate('chat');$('#send-chat').disabled=true;$('#new-chat').disabled=true;
  message('user',question);const loading=message('assistant','正在检索课程依据并组织回答…');loading.classList.add('pending');
  try{const data=await api('/api/chat',{question,mode,history:history.slice(-8)});loading.remove();message('assistant',data.answer,data.sources,data.tool_runs);history.push({role:'user',content:question},{role:'assistant',content:data.answer});history=history.slice(-16);saveChat();}
  catch(e){loading.remove();message('error',e.message);}
  finally{busy=false;$('#send-chat').disabled=false;$('#new-chat').disabled=false;$('#chat-input').focus();}
}
document.addEventListener('click',e=>{const nav=e.target.closest('[data-view]');if(nav)navigate(nav.dataset.view);const quick=e.target.closest('[data-question]');if(quick)sendChat(quick.dataset.question);});
$('.brand').addEventListener('click',e=>{e.preventDefault();navigate('home');});
$('#chat-form').addEventListener('submit',e=>{e.preventDefault();const q=$('#chat-input').value;if(!q.trim()||busy)return;$('#chat-input').value='';sendChat(q);});
$('#chat-input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();$('#chat-form').requestSubmit();}});
$('#home-send').addEventListener('click',()=>{const q=$('#home-input').value;if(!q.trim()){navigate('chat');$('#chat-input').focus();return;}sendChat(q);$('#home-input').value='';});
$('#home-input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.isComposing)$('#home-send').click();});
$('#depth-control').addEventListener('click',e=>{const b=e.target.closest('[data-mode]');if(!b)return;mode=b.dataset.mode;$$('#depth-control button').forEach(x=>x.classList.toggle('selected',x===b));});
$('#new-chat').addEventListener('click',()=>{history=[];saveChat();$('#messages').replaceChildren();message('assistant','新对话已开始。请告诉我你想学习的知识点或输入完整题目。');});
function renderKnowledge(){
  const query=$('#knowledge-search').value.trim();const list=knowledge.filter(c=>(category==='全部'||(category==='公式速查'?!!c.formula:c.category===category))&&(!query||`${c.title}${c.content}${c.conditions}`.includes(query)));
  const root=$('#knowledge-list');root.replaceChildren();if(!list.length){root.append(node('p','empty',knowledge.length?'没有匹配的知识点。':'公开源码版未附带课程知识，请先导入经核验的资料。'));return;}
  for(const c of list){const card=node('article','knowledge-card');card.id=`knowledge-${c.id}`;card.append(node('span','category',c.category),node('h2','',c.title));const p=node('p');p.textContent=c.content.slice(0,95)+(c.content.length>95?'…':'');card.append(p);if(c.formula){const f=node('div','message-content');markdown(f,`$$${c.formula}$$`);card.append(f);}const details=node('details');details.append(node('summary','','阅读完整知识与适用条件'));const text=node('div','message-content');markdown(text,c.content);details.append(text);if(c.conditions)details.append(node('div','condition-note',`适用条件：${c.conditions}`));if(c.symbols){const sy=node('div','message-content');markdown(sy,c.symbols);details.append(sy);}card.append(details);sources(card,[c]);root.append(card);}
}
$('#knowledge-search').addEventListener('input',renderKnowledge);
function renderCategories(){const cats=['全部',...new Set(knowledge.map(c=>c.category))];if(!cats.includes('公式速查'))cats.push('公式速查');const root=$('#categories');root.replaceChildren();for(const name of cats){const b=node('button',name===category?'selected':'',name);b.addEventListener('click',()=>{category=name;renderCategories();renderKnowledge();});root.append(b);}}
$('#calc-tabs').addEventListener('click',e=>{const b=e.target.closest('[data-calc]');if(!b)return;calcType=b.dataset.calc;$$('#calc-tabs button').forEach(x=>x.classList.toggle('selected',x===b));$('#calc-equal').classList.toggle('hidden',calcType!=='equal');$('#calc-cylinder').classList.toggle('hidden',calcType!=='cylinder');});
const fmt=n=>Number(n).toLocaleString('zh-CN',{maximumSignificantDigits:8,useGrouping:false});
$('#calc-form').addEventListener('submit',async e=>{
  e.preventDefault();const button=e.submitter;button.disabled=true;const fields=new FormData(e.target);let name,args;
  try{
    if(calcType==='equal'){name='equal_allocation';args={total:Number(fields.get('total')),coefficients:String(fields.get('coefficients')).split(/[,，\s]+/).filter(Boolean).map(Number)};}
    else{name='cylinder';args={diameter:Number(fields.get('diameter')),height:Number(fields.get('height')),relative_percent:Number(fields.get('relative_percent'))};for(const k of ['diameter_error','height_error'])if(String(fields.get(k)).trim())args[k]=Number(fields.get(k));}
    const data=await api('/api/calculate',{name,arguments:args});const r=data.result;const root=$('#calc-result');root.replaceChildren(node('div','tiny-label','计算笔记 · 已由程序复算'));
    const text=node('div','message-content');
    if(name==='equal_allocation'){
      markdown(text,`### 1. 模型与依据\n按等影响原则，各项输入误差幅值与传递系数绝对值成反比；使用前须确认统计模型。\n$$\\sigma_i=\\frac{\\sigma_y}{\\sqrt n\\,|a_i|}$$\n### 2. 每项影响\n共 ${r.allocated.length} 项，总允许误差 ${fmt(r.total)}，每项影响为 ${fmt(r.contribution)}。`);root.append(text);const table=node('table','result-table');table.innerHTML='<thead><tr><th>分项</th><th>传递系数</th><th>允许误差幅值</th></tr></thead>';const tbody=node('tbody');r.allocated.forEach((x,i)=>{const tr=node('tr');[i+1,fmt(r.coefficients[i]),fmt(x)].forEach(t=>tr.append(node('td','',String(t))));tbody.append(tr);});table.append(tbody);root.append(table);root.append(node('div','result-verdict',`3. 合成验算：${fmt(r.recombined)}，与总允许误差 ${fmt(r.total)} 一致。单位按输入模型确定。`));sources(root,knowledge.filter(c=>c.id==='equal'));
    }else{
      markdown(text,`### 1. 已知与模型\n$D=${args.diameter}$ mm，$h=${args.height}$ mm，体积允许相对误差 ${args.relative_percent}%。取 $\\pi=3.1416$。\n$$V=\\frac{\\pi D^2h}{4}$$\n### 2. 总预算与传递系数\n体积 $V=${fmt(r.volume)}$ mm³；允许体积误差 ${fmt(r.allowed_error)} mm³。\n$a_D=${fmt(r.coefficients[0])}$ mm²，$a_h=${fmt(r.coefficients[1])}$ mm²。\n### 3. 等影响初始分配\n$$\\delta_D=${fmt(r.initial.allocated[0])}\\,\\mathrm{mm},\\quad\\delta_h=${fmt(r.initial.allocated[1])}\\,\\mathrm{mm}$$`);root.append(text);
      if(r.actual_error!==undefined){root.append(node('div',`result-verdict${r.qualified?'':' fail'}`,`4. 实际验算：${fmt(r.actual_error)} mm³ ${r.qualified?'≤':'>'} ${fmt(r.allowed_error)} mm³，${r.qualified?'满足':'不满足'}给定允许误差。`));const p=node('div','message-content');markdown(p,`输入方案的直径相对误差为 ${fmt(r.relative_diameter_percent)}%，高度相对误差为 ${fmt(r.relative_height_percent)}%。\n\n采用一阶、不相关的统计合成模型。本工具按输入参数复算，结论仅在确认的模型条件下成立。`);root.append(p);}sources(root,knowledge.filter(c=>['cylinder','conflict'].includes(c.id)));
    }
    root.append(node('p','field-note','计算按一阶、不相关模型进行。初始分配不是唯一方案，调整后须重新验算。'));if(innerWidth<600)root.scrollIntoView({behavior:'smooth',block:'start'});
  }catch(error){toast(error.message);}finally{button.disabled=false;}
});
function practiceCard(row,index,generated=false){const c=node('article','practice-card');c.append(node('div','practice-meta',`${generated?'智能变式':`练习 ${String(index+1).padStart(2,'0')}`} / ${row.level||row.difficulty}`));const h=node('h2');markdown(h,row.question);c.append(h);const input=node('textarea');input.placeholder='先在这里写下你的思路（不自动评分）…';input.setAttribute('aria-label','练习作答');c.append(input);const details=node('details');details.append(node('summary','','查看答案与解析'));const answer=node('div','practice-answer');const body=node('div','message-content');markdown(body,`**参考答案**\n\n${row.answer}\n\n**解析**\n\n${row.explanation}`);answer.append(body);sources(answer,knowledge.filter(k=>row.source_ids?.includes(k.id)));details.append(answer);c.append(details);return c;}
function renderPractice(){const root=$('#practice-list');root.replaceChildren();const rows=exercises.filter(x=>x.level===level);if(!rows.length)root.append(node('p','empty','未附带课程练习，请先导入有权使用的题目或核验知识库。'));rows.forEach((r,i)=>root.append(practiceCard(r,i)));}
$('#level-control').addEventListener('click',e=>{const b=e.target.closest('[data-level]');if(!b)return;level=b.dataset.level;$$('#level-control button').forEach(x=>x.classList.toggle('selected',x===b));renderPractice();$('#practice-status').replaceChildren();});
$('#generate-practice').addEventListener('click',async()=>{const b=$('#generate-practice');if(b.disabled)return;b.disabled=true;$('#practice-status').replaceChildren(node('div','notice','正在检索课程资料并生成练习，应用题会调用程序核实数值…'));const requestedLevel=level;try{const data=await api('/api/practice',{level:requestedLevel,question:`请生成一道${requestedLevel}层次的误差分配练习，条件完整、答案有依据。`});if(data.practice){$('#practice-status').replaceChildren();const row={...data.practice,level:requestedLevel};exercises.unshift(row);if(requestedLevel===level)$('#practice-list').prepend(practiceCard(row,0,true));else toast(`已生成${requestedLevel}层次练习，请切换查看。`);}}catch(e){$('#practice-status').replaceChildren(node('div','notice',`${e.message} 你仍可使用下面的课程基础练习。`));}finally{b.disabled=false;}});
async function init(){navigate(location.hash.slice(1)||'home');try{const [kb,practice]=await Promise.all([api('/api/knowledge'),api('/api/exercises')]);knowledge=kb.items;exercises=practice.items;$("#generate-practice").disabled=knowledge.length===0;renderCategories();renderKnowledge();renderPractice();for(const r of history){const ids=new Set([...r.content.matchAll(/\[S:([\w-]+)\]/g)].map(x=>x[1]));message(r.role,r.content,knowledge.filter(k=>ids.has(k.id)));}}catch(e){toast(e.message);}}
window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)));
init();
