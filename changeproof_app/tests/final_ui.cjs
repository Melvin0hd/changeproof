// Actual app.js handlers + real loopback HTTP server; a DOM test double, not Chrome.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

(async () => {
  const base = process.argv[2], expected = process.argv[3];
  assert.match(base, /^http:\/\/127\.0\.0\.1:\d+$/);
  const web = path.join(__dirname, '..', 'web');
  const html = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
  class Element {
    constructor() { this.value=''; this.textContent=''; this.children=[]; this.dataset={}; this.disabled=false; this.hidden=false; }
    append(e) { this.children.push(e); }
    replaceChildren(...e) { this.children=[...e]; this.textContent=''; }
    setAttribute(k,v) { this[k]=v; }
    reportValidity() { return true; }
    showModal() { this.open=true; }
    close() { this.open=false; }
    focus() { this.focused=true; }
    select() { this.selected=true; }
    reset() { this.resetDone=true; }
    click() { if(this.href?.startsWith('blob:offline/')) download=blobs.get(this.href); }
  }
  const elements = Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));
  elements.mode.value='demo'; elements.mode.disabled=true; elements.scenario.value='reopen';
  const fields=Object.fromEntries(['vendor','original_decision','assumptions','budget_threshold_usd','monthly_minutes','rate','units','research_question','official_domain'].map(x=>[x,new Element()]));
  elements['decision-form'].elements={namedItem:n=>fields[n]};
  const groups = {'aside dd':Array.from({length:4},()=>new Element()),'aside dt':Array.from({length:4},()=>new Element()),
    '.metrics span':Array.from({length:3},()=>new Element()),'.panel':['impact','evidence','audit'].map(x=>elements[x]),
    '[data-tab]':['impact','evidence','audit'].map(x=>Object.assign(new Element(),{dataset:{tab:x}}))};
  const outcome=new Element(),baselineRate=new Element(),blobs=new Map(); let download;
  const document={getElementById:id=>{assert.ok(elements[id],id);return elements[id];},
    querySelector:s=>{if(s==='.outcome')return outcome;if(s==='.metrics strong')return baselineRate;throw Error(s);},
    querySelectorAll:s=>{assert.ok(groups[s],s);return groups[s];},createElement:()=>new Element()};
  const localFetch=async (url, options)=>{assert.ok(url.startsWith('/api/'));return fetch(base+url,options);};
  const context=vm.createContext({document,window:{confirm:()=>false},fetch:localFetch,Blob,
    URL:{createObjectURL:b=>{const key='blob:offline/'+blobs.size;blobs.set(key,b);return key;},revokeObjectURL:k=>blobs.delete(k)},
    FormData:class {constructor(){this.values=Object.entries(fields).map(([k,v])=>[k,v.value]);}[Symbol.iterator](){return this.values[Symbol.iterator]();}},
    navigator:{clipboard:{writeText:async()=>{throw Error('synthetic clipboard denial');}}},
    setTimeout:fn=>fn()});
  vm.runInContext(fs.readFileSync(path.join(web,'app.js'),'utf8'),context);
  for(let i=0;elements.mode.disabled&&i<200;i++)await new Promise(r=>setTimeout(r,10));
  assert.equal(elements.mode.disabled,false,'actual JS initialization completed');
  elements.mode.value='live'; elements.mode.onchange();
  await elements['live-review'].onclick();
  assert.equal(elements['live-dialog'].open,true);
  await elements['live-confirm'].onclick();
  assert.match(elements['live-summary'].textContent,/Confirm promotional-credit/);
  elements['credits-confirmed'].checked=true;
  await elements['live-confirm'].onclick();
  assert.equal(elements.status.textContent,expected);
  const audit=JSON.parse(elements['audit-json'].textContent);
  assert.equal(audit.mode,'MOCK_LIVE_WORKFLOW');
  assert.equal(audit.original_decision.budget_threshold_usd,700);
  assert.equal(elements['source-link'].children[0].href,audit.evidence.source_url);
  assert.equal(elements['live-review'].disabled,true);
  assert.equal(elements.history.children.length,1);
  assert.ok(!JSON.stringify(audit).includes('synthetic_n'));
  if(audit.outcome.claims.length)assert.equal(audit.outcome.claims[0].raw_claim.evidence_span,audit.extraction_scope.row.text);
  if(expected==='ESCALATE')assert.equal(elements.cost.textContent,'Not calculated');
  else assert.match(elements.delta.textContent,/100[,.]000 minutes/);
  await elements.copy.onclick();
  assert.equal(elements['manual-copy'].selected,true);
  assert.equal(elements['manual-copy'].value,elements['audit-json'].textContent);
  elements.download.onclick();
  assert.deepEqual(JSON.parse(await download.text()),audit);
  elements.history.children[0].onclick();
  assert.equal(JSON.parse(elements['audit-json'].textContent).review_id,audit.review_id);
  await elements['live-confirm'].onclick();
  assert.match(elements.error.textContent,/session_provider_budget_consumed/);
  process.stdout.write(JSON.stringify({ui_logic:'PASS',dom:'test_double_not_browser',decision:expected,
    review_id:audit.review_id,history:true,audit_download_handler:true,manual_copy_fallback:true,
    duplicate_attempt_blocked:true,real_provider_calls:0}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
