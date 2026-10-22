(function(root){
 'use strict';
 const model=typeof module==='object'&&module.exports?require('./model.js'):root.ChangeProofView;
 function freeze(value){if(value&&typeof value==='object'&&!Object.isFrozen(value)){Object.freeze(value);for(const v of Object.values(value))freeze(v);}return value;}
 function relationship(record){
  const rows=record?.outcome?.claims, sources=record?.sources?.length?record.sources:[record?.evidence];
  if(!Array.isArray(rows)||rows.length!==1)return -1;
  const c=rows[0].raw_claim;
  if(!c?.evidence_span||!c.source_id||!c.source_url)return -1;
  const matches=sources.map((s,i)=>s&&s.source_id===c.source_id&&s.source_url===c.source_url&&s.publisher===c.publisher&&typeof s.raw_text==='string'&&s.raw_text.includes(c.evidence_span)?i:-1).filter(i=>i>=0);
  return matches.length===1?matches[0]:-1;
 }
 function project(record,kind){
  if(!['recorded','synthetic','live'].includes(kind))throw Error('Unknown presentation origin');
  const copy=JSON.parse(JSON.stringify(record));
  if(typeof copy.review_id!=='string'||!copy.review_id)throw Error('Missing review identity');
  const v=model.view(copy,kind),index=relationship(copy);
  v.relationshipIndex=index;
  v.presentationKind=kind;
  // Never change a verdict or its original audit. Only suppress unsupported presentation links.
  if(index<0){v.rate=null;v.illustration=null;v.acceptedCalculation=null;}
  return freeze(v);
 }
 const api={project,relationship};if(typeof module==='object'&&module.exports)module.exports=api;else root.ChangeProofPresentation=api;
})(typeof window==='undefined'?globalThis:window);
