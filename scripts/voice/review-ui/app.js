'use strict';
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let data, candidates, current, media, events, state={issues:{},media:{}}, tab='issues', selectedAudio=null, sequence=[], timer=null, generation=0, manifestHash;
const pending=new Map(), queued=new Map(), player=$('#player');
const kindNames={'user-approved':'你已标合适','existing-unrejected':'旧片段 · 未标问题','new-audition':'新找 · 待你听审'};
function savedText(s){$('#save-status').textContent=s;}
function cache(){try{localStorage.setItem('sui-review2-'+manifestHash,JSON.stringify(state));}catch{}}
function searchable(...s){const q=$('#search').value.trim().toLowerCase();return !q||s.join(' ').toLowerCase().includes(q);}
function getIssue(id){return state.issues[id]||{};}
function issueMedia(issue){const all=issue.media_ids.map(id=>media[id]);const chosen=all.filter(m=>m.language===$('#language').value);return chosen.length?chosen:all;}
function labelMedia(m){const name=m.original_source_name.replaceAll('\\','/').split('/').pop();return `${m.language==='Chinese'?'中':'英'} · ${m.media_id} · ${m.original_seconds.toFixed(3)}s · ${name}`;}
function playButton(kind,id,label,extra=''){return `<button class="listen ${extra}" data-play="${kind}" data-id="${esc(id)}">▶ ${label}</button>`;}
function fitMessage(candidate, related){const fits=related.filter(m=>candidate.seconds<=m.v3_cap_seconds+1/48000).length;return fits===related.length?'时长在原 v3 保守上限内':`${related.length-fits}/${related.length} 个槽超原 v3 时长上限 · 安装前需检查事件窗口`;}
function renderIssues(){
  $('#issues').innerHTML=data.issues.filter(i=>searchable(i.old_number,String(i.old_number).padStart(2,'0'),i.title,i.feedback.note,...i.events)).map(i=>{
    const review=getIssue(i.id), related=issueMedia(i),scope=Object.entries(i.language_uses).map(([l,n])=>`${l==='Chinese'?'中文':'英语'} ${n} 个媒体`).join(' / ');
    const route=i.events.map(e=>`<div class="route">${esc(events[e].title)}<br><code>${esc(e)}</code></div>`).join('');
    return `<article class="issue" id="${i.id}" data-issue="${i.id}"><div class="issue-head"><span class="number">#${String(i.old_number).padStart(2,'0')}</span><div><h2>${esc(i.title)}</h2><p class="user-note">你的标注：${esc(i.feedback.note||'听不清')}</p><div class="language-note">${scope}${!i.language_uses.Chinese?' · 当前中文分支没有使用这一段':''}</div>${i.mixed_contexts?'<p class="warning">这段同时用于受击、憋气、出招。可到“按游戏时机对照”分别选用，避免所有动作都用同一声音。</p>':''}</div></div><div class="comparison"><select class="original-select" aria-label="#${i.old_number} 原版媒体">${related.map(m=>`<option value="${m.id}">${esc(labelMedia(m))}</option>`).join('')}</select><button class="listen" data-action="issue-original">▶ 原版魂</button>${playButton('current',i.old_id,'当前 #'+String(i.old_number).padStart(2,'0'),'current-button')}<button class="compare-sequence" data-action="compare">原版 → 当前 → 候选</button></div><details class="issue-more"><summary>这些声音在什么时机用？ · ${i.events.length} 个事件</summary>${route}<p>上方可选择每一个实际原版随机媒体，而非只选一条代表。</p></details><div class="options">${i.suggestions.map(cid=>{
      const c=candidates[cid],rating=review.ratings?.[cid];
      return `<div class="candidate${review.choice===cid?' selected':''}" data-candidate="${cid}"><div><div class="candidate-title">${esc(c.title)}</div><div class="candidate-meta"><span class="tag">${kindNames[c.kind]}</span>${esc(c.label)} · ${c.seconds.toFixed(3)} 秒${c.outer_silence_only?' · 仅去首尾空白':''}${c.rms_dbfs<-28?' · 原录音偏轻，请重点听审':''}</div><div class="candidate-meta ${i.duration_fit[cid].under_v3_cap<i.duration_fit[cid].total?'warning':''}">${esc(fitMessage(c,i.media_ids.map(id=>media[id])))}</div></div><div>${playButton('candidate',cid,'试听')}${c.context_url?`<button class="reject" data-play="context" data-id="${cid}">完整来源</button>`:''}</div><div><button class="choose" data-action="choose" aria-pressed="${review.choice===cid}">${review.choice===cid?'✓ 已选':'选用'}</button><button class="reject" data-action="reject" aria-pressed="${rating==='bad'}">${rating==='bad'?'已排除':'不合适'}</button></div></div>`;
    }).join('')}<div class="choice-tools"><button class="choose" data-action="restore" aria-pressed="${review.choice==='original'}">这些槽恢复原版</button><button class="choose" data-action="defer" aria-pressed="${review.choice==='by-event'}">按事件分别选</button><span class="choice-info">${review.choice==='original'?'方案：恢复原版':review.choice==='by-event'?'方案：逐时机选择':review.choice?'已记下候选，未修改游戏':'尚未选择'}</span></div><textarea class="note" data-note="${i.id}" aria-label="#${i.old_number} 本轮备注" maxlength="2000" placeholder="本轮意见，例如：这个适合受击，但出招还不够有力">${esc(review.note||'')}</textarea></div></article>`;
  }).join('')||'<p class="empty">没有符合搜索的语音。</p>';
}
function effectiveChoice(m){const explicit=state.media[m.id]?.choice;if(explicit)return explicit;const issue=getIssue(m.issue_id);return issue.choice&&issue.choice!=='by-event'?issue.choice:(m.suggestions[0]||'current');}
function renderEvents(){
  const event=events[$('#event-select').value];if(!event)return;
  const rows=data.media.filter(m=>m.language===$('#language').value&&m.events.includes(event.id)&&searchable(m.media_id,m.current_number,m.current_title,m.original_source_name,event.title,event.id));
  $('#event-count').textContent=`${rows.length} 个原版随机媒体`;
  const route=event.air_routes.slice(0,7).map(r=>`${esc(r.ability)} · ${r.start_seconds.toFixed(3)} 秒`).join('<br>');
  $('#event-context').innerHTML=`<strong>${esc(event.title)}</strong>${!event.selected_target?' · 共享媒体同步事件':''}<br><code>${esc(event.id)} · EventID ${event.event_id}</code>${event.air_routes.length?`<details><summary>有 ${event.air_routes.length} 条空中技能时间线引用</summary>${route}${event.air_routes.length>7?'<br>其余引用见本地审计记录':''}</details>`:'<p class="explain">这是按事件名称解释的时机，尚无逐个地面动作的实机触发记录。</p>'}`;
  $('#event-rows').innerHTML=rows.map(m=>{
    const choice=effectiveChoice(m),c=candidates[choice],options=[...new Set([...m.suggestions,...(c?[choice]:[])])];
    return `<article class="media-row${m.issue_id?' issue-media':''}" data-media="${m.id}"><div class="media-cell"><label>原版魂 · ${m.language==='Chinese'?'中文':'英语'}</label><div class="media-title">${esc(m.original_source_name.replaceAll('\\','/').split('/').pop())}</div><div class="media-meta">MediaID ${m.media_id} · ${m.original_seconds.toFixed(3)} 秒</div>${playButton('original',m.id,'原版')}</div><div class="media-cell"><label>当前安装的岁己语音${m.issue_id?' · 你已标问题':''}</label><div class="media-title">#${String(m.current_number).padStart(2,'0')} ${esc(m.current_title)}</div><div class="media-meta">${m.current_seconds.toFixed(3)} 秒</div>${playButton('current',m.current_id,'当前')}</div><div class="media-cell"><label>${state.media[m.id]?.choice?'本媒体单独选择':'候选试听 · 未单独确认时仅作建议'}</label><select class="media-choice" aria-label="MediaID ${m.media_id} 方案"><option value="current" ${choice==='current'?'selected':''}>保留当前岁己声音</option><option value="original" ${choice==='original'?'selected':''}>恢复这一槽的原版魂</option>${options.map(cid=>`<option value="${cid}" ${choice===cid?'selected':''}>${esc(candidates[cid].title)} · ${candidates[cid].seconds.toFixed(3)}s</option>`).join('')}</select><button class="listen" data-action="media-proposal">▶ 候选</button><button class="compare-sequence" data-action="media-compare">A → B → C</button>${c&&c.seconds>m.v3_cap_seconds+1/48000?`<div class="warning">候选 ${c.seconds.toFixed(3)}s，原上限 ${m.v3_cap_seconds.toFixed(3)}s；先听审，安装前再验窗口。</div>`:''}</div></article>`;
  }).join('')||'<p class="empty">此语言 / 搜索条件下没有媒体。</p>';
}
function renderCurrent(){
  $('#current-rows').innerHTML=data.current.filter(r=>searchable(r.number,String(r.number).padStart(2,'0'),r.title,r.round1.note,r.id)).map(r=>{
    const issue=data.issues.find(i=>i.old_id===r.id),status=r.round1.status;
    return `<article class="current-row" data-current="${r.id}"><div><h3><span class="number">#${String(r.number).padStart(2,'0')}</span> ${esc(r.title)} · 片段 ${r.segment}</h3><p>${r.seconds.toFixed(3)} 秒 · ${r.events.length} 个事件 · <span class="${issue?'issue-flag':''}">${issue?'待替换':status==='good'?'你已标合适':'未标问题'}</span>${r.round1.note?' · '+esc(r.round1.note):''}</p></div><div class="actions">${playButton('current',r.id,'当前')}<button class="listen" data-action="current-original">看原版对照</button>${issue?`<button class="listen" data-action="go-issue">看新候选</button>`:''}</div></article>`;
  }).join('')||'<p class="empty">没有符合搜索的语音。</p>';
}
function progress(){const n=data.issues.filter(i=>getIssue(i.id).choice).length;$('#decided').textContent=`${n} / ${data.issues.length}`;}
function render(){if(!data)return;if(tab==='issues')renderIssues();else if(tab==='events')renderEvents();else renderCurrent();progress();}
function setTab(value){tab=value;document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===value));$('#issues-view').hidden=value!=='issues';$('#events-view').hidden=value!=='events';$('#current-view').hidden=value!=='current';render();}
function cancel(){clearTimeout(timer);timer=null;generation++;sequence=[];}
function audioSpec(kind,id){
  if(kind==='context'){const c=candidates[id];return {url:c.context_url,kind:'新候选完整来源 · 未裁首尾',title:c.title,detail:'用来确认上下文；不是已装入游戏的片段。'};}
  if(kind==='original'){const m=media[id];return {url:m.original_url,kind:'原版魂 · '+(m.language==='Chinese'?'中文':'英语'),title:events[m.events[0]].title,detail:`MediaID ${m.media_id} · ${m.original_seconds.toFixed(3)} 秒 · 原始 WEM 解码`};}
  if(kind==='current'){const r=current[id];return {url:r.url,kind:'当前岁己 · 游戏 WEM 解码',title:`#${String(r.number).padStart(2,'0')} ${r.title}`,detail:`片段 ${r.segment} · ${r.seconds.toFixed(3)} 秒`};}
  const c=candidates[id];return {url:c.url,kind:'新方案试听 · '+kindNames[c.kind],title:c.title,detail:`${c.label} · ${c.seconds.toFixed(3)} 秒 · 未装入游戏`};
}
async function start(spec){
  if(!spec)return;const token=generation;selectedAudio=spec;player.src=spec.url;$('#playing-kind').textContent=spec.kind;$('#playing-title').textContent=spec.title;$('#playing-detail').textContent=spec.detail;$('#audio-error').textContent='';
  try{await player.play();}catch(e){if(e.name!=='AbortError'&&token===generation)$('#audio-error').textContent='未能播放：'+e.message;}
}
function play(kind,id){cancel();start(audioSpec(kind,id));}
function proposal(m){const choice=effectiveChoice(m);return choice==='original'?audioSpec('original',m.id):choice==='current'?audioSpec('current',m.current_id):audioSpec('candidate',choice);}
function compare(m,choice){cancel();$('#loop').checked=false;sequence=[audioSpec('current',m.current_id),choice||proposal(m)];start(audioSpec('original',m.id));}
player.addEventListener('ended',()=>{const token=generation;if(sequence.length){timer=setTimeout(()=>{if(token===generation)start(sequence.shift());},800);}else if($('#loop').checked&&selectedAudio){timer=setTimeout(()=>{if(token===generation)start(selectedAudio);},650);}});
player.addEventListener('error',()=>{if(player.getAttribute('src'))$('#audio-error').textContent='音频加载失败，请刷新后重试。';});
$('#stop').addEventListener('click',()=>{cancel();player.pause();player.currentTime=0;});
$('#loop').addEventListener('change',cancel);
$('#volume').addEventListener('input',()=>{player.volume=Number($('#volume').value);$('#volume-label').textContent=Math.round(player.volume*100)+'%';});
async function persist(scope,id){
  const key=scope+':'+id;clearTimeout(pending.get(key));pending.delete(key);cache();
  const item=structuredClone(state[scope][id]||{});savedText('正在保存…');
  const task=(queued.get(key)||Promise.resolve()).catch(()=>{}).then(async()=>{
    try{const r=await fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({manifest_sha256:manifestHash,scope,id,item})});if(!r.ok)throw new Error();savedText('本轮标记已保存到本机');}
    catch{savedText('已存浏览器 · 请导出备份');}
  });queued.set(key,task);await task;
}
function change(scope,id,patch){state[scope][id]={...(state[scope][id]||{}),...patch,updated_at:new Date().toISOString()};cache();persist(scope,id);render();}
document.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b)return;
  if(b.dataset.tab){setTab(b.dataset.tab);return;}
  if(b.dataset.play){play(b.dataset.play,b.dataset.id);return;}
  const issueEl=b.closest('[data-issue]'),mediaEl=b.closest('[data-media]');
  if(issueEl){const issue=data.issues.find(i=>i.id===issueEl.dataset.issue),cid=b.closest('[data-candidate]')?.dataset.candidate,review=getIssue(issue.id),original=media[issueEl.querySelector('.original-select').value];
    if(b.dataset.action==='issue-original')play('original',original.id);
    if(b.dataset.action==='compare'){const chosen=candidates[review.choice]?audioSpec('candidate',review.choice):review.choice==='original'?audioSpec('original',original.id):audioSpec('candidate',issue.suggestions[0]);compare(original,chosen);}
    if(b.dataset.action==='choose')change('issues',issue.id,{choice:review.choice===cid?null:cid,ratings:{...review.ratings,[cid]:'good'}});
    if(b.dataset.action==='reject')change('issues',issue.id,{choice:review.choice===cid?null:review.choice,ratings:{...review.ratings,[cid]:review.ratings?.[cid]==='bad'?null:'bad'}});
    if(b.dataset.action==='restore')change('issues',issue.id,{choice:review.choice==='original'?null:'original'});
    if(b.dataset.action==='defer')change('issues',issue.id,{choice:review.choice==='by-event'?null:'by-event'});
  }
  if(mediaEl){const m=media[mediaEl.dataset.media];if(b.dataset.action==='media-proposal')startWithCancel(proposal(m));if(b.dataset.action==='media-compare')compare(m);}
  const currentEl=b.closest('[data-current]');if(currentEl){const r=current[currentEl.dataset.current],issue=data.issues.find(i=>i.old_id===r.id);
    if(b.dataset.action==='current-original'){const related=data.media.filter(m=>m.current_id===r.id),m=related.find(m=>m.language===$('#language').value)||related[0];$('#language').value=m.language;$('#event-select').value=m.events[0];setTab('events');document.getElementById('events-view').scrollIntoView({block:'start'});}
    if(b.dataset.action==='go-issue'&&issue){setTab('issues');document.getElementById(issue.id).scrollIntoView({block:'start',behavior:'smooth'});}
  }
});
function startWithCancel(spec){cancel();start(spec);}
document.addEventListener('change',e=>{if(e.target.matches('.media-choice')){const id=e.target.closest('[data-media]').dataset.media;change('media',id,{choice:e.target.value});}});
document.addEventListener('input',e=>{
  if(!e.target.matches('[data-note]'))return;const id=e.target.dataset.note;
  state.issues[id]={...getIssue(id),note:e.target.value,updated_at:new Date().toISOString()};cache();const key='issues:'+id;clearTimeout(pending.get(key));pending.set(key,setTimeout(()=>persist('issues',id),450));
});
document.addEventListener('focusout',e=>{if(e.target.matches('[data-note]'))persist('issues',e.target.dataset.note);});
$('#language').addEventListener('change',render);$('#event-select').addEventListener('change',render);$('#search').addEventListener('input',render);
$('#export').addEventListener('click',()=>{const blob=new Blob([JSON.stringify({manifest_sha256:manifestHash,source_report_sha256:data.source_report_sha256,exported_at:new Date().toISOString(),...state},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='岁己语音-二审与原版对照.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),10000);});
window.addEventListener('beforeunload',()=>{cache();for(const key of pending.keys()){const [scope,id]=key.split(':');navigator.sendBeacon('/api/review',new Blob([JSON.stringify({manifest_sha256:manifestHash,scope,id,item:state[scope][id]})],{type:'application/json'}));}});
async function init(){
  try{
    const response=await fetch('manifest.json',{cache:'no-store'});if(!response.ok)throw new Error('清单读取失败');const text=await response.text();data=JSON.parse(text);manifestHash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
    candidates=Object.fromEntries(data.candidates.map(c=>[c.id,c]));current=Object.fromEntries(data.current.map(c=>[c.id,c]));media=Object.fromEntries(data.media.map(c=>[c.id,c]));events=Object.fromEntries(data.events.map(c=>[c.id,c]));
    let remote={issues:{},media:{}};try{const r=await fetch('/api/review');if(!r.ok)throw new Error();const result=await r.json();if(result.manifest_sha256!==manifestHash)throw new Error();remote=result;savedText('本轮标记保存在本机');}catch{savedText('标记保存在浏览器 · 可导出');}
    let local;try{local=JSON.parse(localStorage.getItem('sui-review2-'+manifestHash)||'{}');}catch{local={};}
    for(const scope of ['issues','media']){for(const [id,item] of Object.entries(remote[scope]||{}))state[scope][id]=item;for(const [id,item] of Object.entries(local[scope]||{})){if(!state[scope][id]||(item.updated_at||'')>(state[scope][id].updated_at||''))state[scope][id]=item;}}
    $('#event-select').innerHTML=data.events.map(e=>`<option value="${esc(e.id)}">${esc(e.title)}${!e.selected_target?'（共享）':''}</option>`).join('');
    player.volume=.6;render();
  }catch(e){$('#issues').textContent='加载失败：'+e.message;savedText('请确认本地服务正在运行');}
}
init();
