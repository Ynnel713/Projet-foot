"""Diagnostic du ticket v2-realisme/18n (partie 2) : à temps du ballon égal jusqu'à l'adversaire, passes courtes
(< 15 m) et longues coupées au même taux ? Lots d'ajustement de `18m-diag-script.py`.
Usage : uv run python .scratch/v2-realisme/mesures/18n-diagnostic-temps.py DOSSIER"""
import sys
import json,glob,math,sys
sys.path.insert(0,'.')
from collections import defaultdict
import v2engine.possession as P
D=sys.argv[1]  # dossier des sorties de 18m-diag-script.py (fit-*.json, ctrl-*.json)
R=[r for p in sorted(glob.glob(D+'/fit-*.json')) for r in json.load(open(p))]
lf=math.log(P.BALL_FRICTION_PER_S)
print("v0 à 5/10/20/30/40 m :",[round(P._launch_speed(x),1) for x in (5,10,20,30,40)])
def tball(L,along):
    v0=P._launch_speed(max(L,0.1)); v=max(P.BALL_STOPPED_MPS,v0+max(along,0)*lf)
    return math.log(v/v0)/lf
T=[0.05,0.1,0.15,0.2,0.3,0.45,0.7,1.0,9]
for zone in ("près","traj"):
    for g in ([0.5,1,2] if zone=="près" else [1,2,3,4,6]):
        n=defaultdict(int);h=defaultdict(int)
        for r in R:
            for o in r["opp"]:
                if o["cut"]<=0: continue
                if (o["along"]<=3)!=(zone=="près"): continue
                gg=next((x for x in ([0.5,1,2,3,4,6]) if o["gap"]<x),None)
                if gg!=g: continue
                t=tball(r["L"],o["along"]); b=next(x for x in T if t<x)
                # long vs short split to test whether length matters at equal time
                k=(b,r["L"]<15); n[k]+=1; h[k]+=r.get("first")==o["n"]
        print(f"{zone} <{g} m : "+"  ".join(f"t<{b}: court {h[(b,True)]/n[(b,True)]:.2f}({n[(b,True)]}) long {h[(b,False)]/n[(b,False)]:.2f}({n[(b,False)]})" if n[(b,True)]>=40 and n[(b,False)]>=40 else (f"t<{b}: {(h[(b,True)]+h[(b,False)])/max(1,n[(b,True)]+n[(b,False)]):.2f}({n[(b,True)]+n[(b,False)]})") for b in T))
