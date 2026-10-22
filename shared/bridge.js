(function(){
 'use strict';
 let current=null,frame=null,shown=false,ready=false,identity=null,cancel,complete;
 const protocol='changeproof.presentation.v1';
 const el=id=>document.getElementById(id);
 function send(action){if(frame?.contentWindow)frame.contentWindow.postMessage({protocol,action,record:current?.original,kind:current?.presentationKind,reduced:el('reduce-motion')?.checked},location.origin);}
 function close(){if(!shown)return;send('pause');shown=false;el('spatial-view').hidden=true;el('app').hidden=false;el('explore').focus({preventScroll:true});el('review-stage').scrollIntoView({block:'start',behavior:'instant'});}
 function open(){if(!current)return;cancel();complete();shown=true;el('app').hidden=true;el('spatial-view').hidden=false;
  el('spatial-identity').textContent='Review '+current.original.review_id+' / '+current.label+' / '+current.status;
  el('spatial-view').scrollIntoView({block:'start',behavior:'instant'});el('return-decision').focus({preventScroll:true});
  if(!frame){frame=document.createElement('iframe');frame.id='spatial-frame';frame.title='Spatial Investigation of the same ChangeProof review';frame.src='../spatial/index.html';frame.addEventListener('load',()=>{ready=true;send('present');});el('spatial-body').append(frame);}
  else if(ready){if(identity!==current.original.review_id)send('present');else send('preferences');}
 }
 window.addEventListener('message',e=>{if(e.source!==frame?.contentWindow||e.origin!==location.origin||e.data?.protocol!==protocol)return;
  if(e.data.action==='return')close();
  if(e.data.action==='preference_changed')el('reduce-motion').checked=!!e.data.reduced;
  if(e.data.action==='presented'&&e.data.review_id===current?.original.review_id){identity=e.data.review_id;el('spatial-status').textContent='Same audit loaded. No new provider request.';}
 });
 document.addEventListener('keydown',e=>{if(shown&&e.key==='Escape')close();});
 window.ChangeProofSpatial={mount(stop,finish){cancel=stop;complete=finish;
   document.querySelector('.design-link').hidden=true;
   const b=document.createElement('button');b.id='explore';b.className='quiet';b.innerHTML='<i data-lucide="scan-search" aria-hidden="true"></i> Explore evidence';b.disabled=true;b.onclick=open;
   document.querySelector('.result-actions').prepend(b);
   const region=document.createElement('section');region.id='spatial-view';region.hidden=true;region.setAttribute('aria-label','Spatial Investigation');
   region.innerHTML='<div class="spatial-nav"><button id="return-decision" class="quiet"><i data-lucide="arrow-left" aria-hidden="true"></i> Decision Flow</button><div><h1>Explore the same evidence</h1><p id="spatial-identity"></p><p id="spatial-status" role="status">Opening a read-only view. No new execution.</p></div></div><div id="spatial-body"></div>';
   document.body.append(region);el('return-decision').onclick=close;},
  set(view){current=view;identity=null;if(el('explore'))el('explore').disabled=false;},
  clear(){if(shown)close();current=null;identity=null;if(frame)send('pause');if(el('explore'))el('explore').disabled=true;}
 };
})();
