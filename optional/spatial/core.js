(function(root){'use strict';
 function sourceForClaim(record){const url=record.evidence.source_url;const list=record.sources?.length?record.sources:[record.evidence];return Math.max(0,list.findIndex(s=>s.source_url===url));}
 function stageAt(ms){return ms<1500?0:ms<3500?1:2;}
 function position(elapsed,delta){return Math.min(5500,Math.max(0,elapsed+Math.max(0,delta)));}
 function documentParts(source,span){const text=source.raw_text||'No excerpt was preserved for this reference.';const pos=span?text.indexOf(span):-1;return pos<0?{before:text,span:'',after:''}:{before:text.slice(0,pos),span,after:text.slice(pos+span.length)};}
 const api={sourceForClaim,stageAt,position,documentParts};if(typeof module==='object'&&module.exports)module.exports=api;else root.SpatialCore=api;
})(typeof window==='undefined'?globalThis:window);
