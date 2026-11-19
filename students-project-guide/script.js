const links=[...document.querySelectorAll('.links a')],secs=links.map(a=>document.querySelector(a.hash));
const nav=document.querySelector('nav');
function spy(){const y=scrollY+120;let i=0;secs.forEach((s,n)=>{if(s.offsetTop<=y)i=n});
 links.forEach((a,n)=>a.classList.toggle('on',n===i));
 const h=document.documentElement;document.querySelector('#bar div').style.width=(scrollY/(h.scrollHeight-innerHeight)*100)+'%'}
addEventListener('scroll',spy,{passive:true});spy();
document.getElementById('menu').onclick=()=>nav.classList.toggle('open');
links.forEach(a=>a.addEventListener('click',()=>nav.classList.remove('open')));
document.getElementById('find').addEventListener('input',e=>{const q=e.target.value.toLowerCase();
 links.forEach((a,n)=>{a.style.display=(!q||(a.textContent+secs[n].textContent).toLowerCase().includes(q))?'':'none'})});
document.querySelectorAll('pre').forEach(p=>{const b=document.createElement('button');b.className='copy';b.textContent='Copy';
 b.onclick=async()=>{try{await navigator.clipboard.writeText(p.innerText.replace(/^Copy\n?/,''));b.textContent='Copied'}catch{b.textContent='Press Ctrl+C'}setTimeout(()=>b.textContent='Copy',1500)};p.appendChild(b)});
const boxes=[...document.querySelectorAll('.chk input')],out=document.getElementById('prog'),K='sheetwise-checks';
try{const s=JSON.parse(localStorage.getItem(K)||'[]');boxes.forEach((b,i)=>b.checked=!!s[i])}catch{}
function upd(){out.textContent=boxes.filter(b=>b.checked).length+' of '+boxes.length+' steps done';
 try{localStorage.setItem(K,JSON.stringify(boxes.map(b=>b.checked)))}catch{}}
boxes.forEach(b=>b.onchange=upd);upd();
/* scroll reveal */
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:.08});
document.querySelectorAll('section,.stat').forEach(s=>{s.classList.add('reveal');io.observe(s)});
/* counters */
const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
const co=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;const el=e.target.querySelector('b'),n=+el.dataset.n;co.unobserve(e.target);
 if(reduce){el.textContent=n.toLocaleString();return}let t0;const step=t=>{t0=t0||t;const p=Math.min((t-t0)/1200,1);el.textContent=Math.round(n*(1-Math.pow(1-p,3))).toLocaleString();if(p<1)requestAnimationFrame(step)};requestAnimationFrame(step)}),{threshold:.5});
document.querySelectorAll('.stat').forEach(s=>co.observe(s));
/* typing hero */
const txt="# Question: total Sales by Category\nresult = (df\n  .groupby('Category')['Sales']\n  .sum()\n  .reset_index())\n\n# Result: 2 rows -> table + chart";
const tp=document.getElementById('typed');
if(reduce)tp.textContent=txt;else{let i=0;(function t(){tp.textContent=txt.slice(0,++i);if(i<txt.length)setTimeout(t,35);else setTimeout(()=>{i=0;t()},4000)})()}
/* back to top */
const top_=document.getElementById('top');addEventListener('scroll',()=>top_.classList.toggle('show',scrollY>600),{passive:true});
top_.onclick=()=>scrollTo({top:0,behavior:reduce?'auto':'smooth'});
