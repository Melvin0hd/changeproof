from dataclasses import replace
from models import *

def evaluate(state,new_claims):
    old={c.proposition:c for c in state.evidence}; deltas=[]; mapped=set(); contradictions=[]
    for c in new_claims:
        if c.incomplete: typ='CONTRADICTORY'; contradictions.append(c.claim_id)
        elif not c.criteria: typ='IRRELEVANT'
        elif c.proposition in old and old[c.proposition].value==c.value: typ='DUPLICATE'
        elif c.proposition in old: typ='CHANGED'
        else: typ='NEW'
        deltas.append({'claim_id':c.claim_id,'type':typ,'old':old.get(c.proposition).value if c.proposition in old else None,'new':c.value})
        if typ in ('NEW','CHANGED'): mapped.update(c.criteria)
    criteria={c.criterion_id:c for c in state.criteria}; calc={}; crossed=False
    rate=next((c for c in new_claims if c.proposition=='fee_rate'),None)
    if rate and 'C01' in mapped:
        cost=state.facts['minutes']*float(rate.value); crossed=cost>criteria['C01'].threshold.value
        calc={'monthly_cost':{'minutes':state.facts['minutes'],'rate':rate.value,'result':cost,'threshold':100,'operator':'gt','crossed':crossed}}
        criteria['C01']=replace(criteria['C01'],current_value=cost)
    for cid in mapped-{'C01'}:
        value=next(c.value for c in reversed(new_claims) if cid in c.criteria); criteria[cid]=replace(criteria[cid],current_value=value)
    if contradictions: status='ESCALATE'; qualifier='incomplete_or_contradictory'; reasons=('decision_evidence_unresolved',)
    elif crossed: status='REOPEN'; qualifier=None; reasons=('hard_threshold_crossed',)
    else: status='KEEP'; qualifier='future_pricing_unresolved' if any(c.value=='postponed' for c in new_claims) else None; reasons=('no_material_transition',)
    nxt=DecisionState(status,tuple(criteria[k] for k in sorted(criteria)),state.evidence+tuple(c for c,d in zip(new_claims,deltas) if d['type'] not in ('DUPLICATE','IRRELEVANT')),state.facts,state.gaps,state.version+1)
    unaffected=tuple(sorted(set(criteria)-mapped))
    return DecisionTransition(state.status,status,qualifier,tuple(deltas),tuple(sorted(mapped)),unaffected,calc,tuple(contradictions),reasons,nxt,status=='ESCALATE')
