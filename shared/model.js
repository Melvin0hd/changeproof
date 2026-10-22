(function(root){
  'use strict';
  function view(record,kind){
    if(!record || !record.outcome || !['KEEP','REOPEN','ESCALATE'].includes(record.outcome.decision))throw new Error('Invalid decision response. Review stopped.');
    const o=record.outcome,d=record.original_decision;
    if(!d||!Array.isArray(o.claims)||!record.evidence)throw new Error('Incomplete audit response. Review stopped.');
    const row=o.claims.length===1?o.claims[0]:null,claim=row?row.raw_claim:null;
    const calc=o.trace&&o.trace.calculations&&o.trace.calculations.monthly_cost;
    const errors=Array.from(new Set(o.validation_errors||[]));
    const literal=!!(claim&&claim.evidence_span&&record.evidence.raw_text.includes(claim.evidence_span)&&claim.source_url===record.evidence.source_url&&claim.publisher===record.evidence.publisher&&!(row.validation_errors||[]).some(e=>e!=='mapping_requires_review')&&!errors.some(e=>e==='ungrounded_span'||e.startsWith('extraction_or_validation_failure')));
    const rate=literal&&claim.unit==='usd_per_minute'&&typeof claim.normalized_value==='number'&&Number.isFinite(claim.normalized_value)?claim.normalized_value:null;
    const illustration=rate===null?null:rate*d.monthly_minutes;
    const synthetic=record.mode==='OFFLINE_DEMO',mock=record.mode==='MOCK_LIVE_WORKFLOW';
    const label=kind==='recorded'?'RECORDED PROVIDER EVIDENCE':mock?'OFFLINE QA / MOCKED TRANSPORT':synthetic?'SYNTHETIC OFFLINE EXAMPLE':'FRESH LIVE PROVIDER ATTEMPT';
    const reasons={KEEP:'The supplied evidence does not cross this decision’s cost threshold. Other supplier risks remain outside this check.',REOPEN:'The accepted rate crosses the declared monthly limit. Revisit the original decision before taking action.',ESCALATE:record.failure?'The review could not complete. No price or decision assumption has been accepted.':literal?'The claim is traceable, but applicability is unresolved. A human must check the missing conditions.':'Evidence is incomplete or failed validation. No unsupported assumption is accepted.'};
    return {status:o.decision,label,claim,rate,illustration,acceptedCalculation:calc||null,errors,decision:d,evidence:record.evidence,
      sources:record.sources&&record.sources.length?record.sources:[record.evidence],reason:reasons[o.decision],failure:record.failure||null,
      next:o.decision==='ESCALATE'?'Confirm included minutes, effective date and contract applicability.':'Verify the full source and contract before changing a supplier.',
      original:record,reviewedAt:record.reviewed_at};
  }
  async function copyAudit(record,write,fallback,status){const text=JSON.stringify(record,null,2);try{await write(text);status.textContent='Audit copied.';return 'copied';}catch{fallback.hidden=false;fallback.value=text;fallback.focus();fallback.select();status.textContent='Selected for manual copy.';return 'manual';}}
  const api={view,copyAudit};if(typeof module==='object'&&module.exports)module.exports=api;else root.ChangeProofView=api;
})(typeof window==='undefined'?globalThis:window);
