"""Ajustement du ticket v2-realisme/18n : table de coupe distance à la trajectoire x temps du ballon jusqu'à l'adversaire
(estimateur séquentiel : adversaires rangés par avancée, comptés tant qu'aucun plus près du passeur n'a touché le
ballon), parts non perdues par bande réajustées par moindres carrés (plafond 0,99), contrôle hors ligne sur les lots de
contrôle (7 tranches, par longueur, par Passing). Écrit la table dans tab.json (dossier courant).
Usage : uv run python .scratch/v2-realisme/mesures/18n-ajustement.py DOSSIER"""
import sys
import json,glob,math,sys
sys.path.insert(0,'.')
from collections import defaultdict
import v2engine.possession as P
D=sys.argv[1]  # dossier des sorties de 18m-diag-script.py (fit-*.json, ctrl-*.json)
FIT=[r for p in sorted(glob.glob(D+'/fit-*.json')) for r in json.load(open(p))]
CT=[r for p in sorted(glob.glob(D+'/ctrl-*.json')) for r in json.load(open(p))]
lf=math.log(P.BALL_FRICTION_PER_S)
SH=[0.99,0.98,0.98,0.70]
G=[0.5,1,2,3,4,6]; T=[0.05,0.1,0.15,0.2,0.3,0.45,0.7,1.0,math.inf]
def tball(L,along):
    v0=P._launch_speed(max(L,0.1)); v=max(P.BALL_STOPPED_MPS,v0+max(along,0)*lf)
    return math.log(v/v0)/lf
def lost(r):
    if r.get("first"): return r["first_team"]!=r["team"]
    return bool(r.get("out")) and r.get("out_team")!=r["team"]
def cell(r,o):
    if o["cut"]<=0: return None
    g=next((x for x in G if o["gap"]<x),6); t=next(x for x in T if tball(r["L"],o["along"])<x)
    return g,t
n=defaultdict(int);h=defaultdict(int)
SEQ = True
for r in FIT:
    ops=sorted((o for o in r["opp"] if cell(r,o)), key=lambda o: o["along"])
    for o in ops:
        c=cell(r,o)
        n[c]+=1; hit=r.get("first")==o["n"]; h[c]+=hit
        if SEQ and hit: break  # séquentiel : les adversaires plus loin n'ont pas eu le ballon
tab={c:h[c]/n[c] for c in n}
print("table gap x t (part qui touche le premier, n):")
for g in G: print(f" <{g}: "+" ".join(f"{tab.get((g,t),float('nan')):.2f}({n[(g,t)]})" for t in T))
def keep_new(r):
    k=1.0
    for o in r["opp"]:
        c=cell(r,o)
        if c: k*=1-tab.get(c,0.0)
    return k
def bandpart(r,sh): return sum(w*s for w,s in zip(r["w"],sh))
# refit band shares: scale so mean matches on FIT per band via simple LSQ on 4 shares (capped 0.99)
import itertools
def pred(r,sh): return keep_new(r)*bandpart(r,sh)
for R in (FIT,CT):
    for r in R: r["kn"]=keep_new(r)
# least squares on per-pass: minimise sum (kn*sum w s - notlost)^2 => linear in s
import numpy as np
X=np.array([[r["kn"]*w for w in r["w"]] for r in FIT]); y=np.array([0.0 if lost(r) else 1.0 for r in FIT])
s,*_=np.linalg.lstsq(X,y,rcond=None); print("parts LSQ brutes",np.round(s,3)); s=np.minimum(s,0.99)
print("parts retenues",np.round(s,3))
def report(R,f,label):
    print(label)
    for lo,hi in [(0,8),(8,15),(15,30),(30,99)]:
        S=[r for r in R if lo<=r["L"]<hi]; p=sum(map(f,S))/len(S); o=sum(not lost(r) for r in S)/len(S)
        print(f"   L {lo}-{hi}: n {len(S)} év {p:.3f} obs {o:.3f} écart {100*(p-o):+.1f} ± {196*math.sqrt(o*(1-o)/len(S)):.1f}")
    b=defaultdict(list)
    for r in R: b[min(6,int(f(r)*7))].append(r)
    worst=0
    for k in sorted(b):
        S=b[k]; p=sum(map(f,S))/len(S); o=sum(not lost(r) for r in S)/len(S)
        if len(S)>=500: worst=max(worst,abs(p-o))
        print(f"   [{k/7:.2f};{(k+1)/7:.2f}[ n {len(S)} év {p:.3f} obs {o:.3f} écart {100*(p-o):+.1f} ± {196*math.sqrt(o*(1-o)/len(S)):.1f}")
    p=sum(map(f,R))/len(R); o=sum(not lost(r) for r in R)/len(R)
    print(f"   toutes écart {100*(p-o):+.2f} ; pire tranche {100*worst:.1f}")
    for nm,sel in (("Passing<50",lambda r:r["passing"]<50),(">=70",lambda r:r["passing"]>=70)):
        S=[r for r in R if sel(r)]; p=sum(map(f,S))/len(S); o=sum(not lost(r) for r in S)/len(S)
        print(f"   {nm}: n {len(S)} écart {100*(p-o):+.1f} ± {196*math.sqrt(o*(1-o)/len(S)):.1f}")
report(CT,lambda r:r["chance"],"CONTRÔLE, chance actuelle")
report(CT,lambda r:r["kn"]*bandpart(r,s),"CONTRÔLE, table gap x temps + parts réajustées")
json.dump({"tab":{f"{g}|{t}":v for (g,t),v in tab.items()},"n":{f"{g}|{t}":v for (g,t),v in n.items()},"parts":list(s)},open('tab.json','w'))
