(function(){
 'use strict';
 const copy=v=>JSON.parse(JSON.stringify(v)),data=window.ChangeProofFixtures;
 const extras=[['empty','Saved QA: empty retrieval'],['conflicting','Saved QA: conflicting prices'],['tavily_timeout','Saved QA: technical failure']];
 for(const [value,label]of extras)data.config.scenarios[value]={text:label};
 window.ChangeProofTransport={async request(path,body){
  if(path==='/api/config'&&!body)return copy(data.config);
  if(path==='/api/recorded'&&!body)return copy(data.recorded);
  if(path==='/api/review'&&body?.mode==='demo'&&Object.hasOwn(data.reports,body.scenario))return copy(data.reports[body.scenario]);
  throw Error('Static demo: no live execution, editing or network transport is available.');
 }};
 window.addEventListener('DOMContentLoaded',()=>{
  const $=id=>document.getElementById(id);
  $('mode').querySelector('[value="live"]').remove();
  for(const [value,label]of extras){
   const o=document.createElement('option');o.value=value;o.textContent=label;$('scenario').append(o);data.config.scenarios[value]={text:label};
  }
  const p=document.createElement('p');p.className='static-notice';p.textContent='NO-KEY RECORDED DEMO / Saved engine results, not new provider activity. Synthetic controls and mocked failures are explicitly labeled. Baselines are fixed in this static build.';
  document.querySelector('main').prepend(p);
  $('edit').hidden=true;document.querySelector('.design-link').hidden=true;
 });
})();
