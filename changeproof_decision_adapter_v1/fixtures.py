from models import *
def baseline(minutes=100000):
    cs=(Criterion('C01',0,Threshold('gt',100)),Criterion('C02',8),Criterion('C03','known'),Criterion('C04','record'),Criterion('C05','normal'),Criterion('C06','no_charge'),Criterion('C07','unknown'))
    ev=(EvidenceClaim('rate','fee_rate',0,('C01',)),EvidenceClaim('status','fee_status','not_effective',('C05','C06')))
    return DecisionState('KEEP',cs,ev,{'minutes':minutes},('quota','contract'))
EVENT1=(EvidenceClaim('rate','fee_rate',.002,('C01',)),EvidenceClaim('status','fee_status','announced',('C05','C06','C07')))
EVENT2=(EvidenceClaim('rate','fee_rate',0,('C01',)),EvidenceClaim('status','fee_status','postponed',('C05','C06','C07')))
FALSE_ALARM=(EvidenceClaim('ui','ui_navigation','improved'),)
INCOMPLETE=(EvidenceClaim('scope','fee_scope','possibly_changed',('C01',),True),)
