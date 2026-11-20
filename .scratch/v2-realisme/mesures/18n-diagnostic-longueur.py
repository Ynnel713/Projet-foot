"""Diagnostic du ticket v2-realisme/18n (partie 1) : écart chance évaluée / non perdue par longueur de passe, décomposé en
coupe (1 - produit de coupe, contre pertes au profit d'un adversaire compté par la table) et reste (bandes d'écart) ;
part des adversaires comptés qui touchent le premier, par tranche de distance à la trajectoire et de longueur.
Données : sorties de `18m-diag-script.py` (lots fit-2200, -2206, -2212, -2218 : 6 matchs chacun, `18m-diag-script.py 6 2200`
etc. ; ctrl-2300, -2312, -2324, -2336 : 12 matchs chacun). Usage : uv run python .scratch/v2-realisme/mesures/18n-diagnostic-longueur.py DOSSIER"""
import sys
import json,sys,glob,math
from collections import defaultdict
D=sys.argv[1]  # dossier des sorties de 18m-diag-script.py (fit-*.json, ctrl-*.json)
R=[r for p in sorted(glob.glob(D+'/fit-*.json')+glob.glob(D+'/ctrl-*.json')) for r in json.load(open(p))]
SH=(0.99,0.98,0.98,0.70)
def lost(r):
    if r.get("first"): return r["first_team"]!=r["team"]
    return bool(r.get("out")) and r.get("out_team")!=r["team"]
def cause(r):
    if not lost(r): return None
    if not r.get("first"): return "out"
    o=next((o for o in r["opp"] if o["n"]==r["first"]),None)
    return "cut" if (o and o["cut"]>0) else "other"
LB=[(0,8),(8,12),(12,15),(15,20),(20,25),(25,30),(30,99)]
print(f"{'L':>7} {'n':>6} {'év':>6} {'obs':>6} {'écart':>6} | {'1-keep':>6} {'perte coupe':>11} | {'reste prévu':>11} {'reste obs':>9} | w0 w1 w2 w3")
for lo,hi in LB:
    S=[r for r in R if lo<=r["L"]<hi]
    n=len(S)
    ev=sum(r["chance"] for r in S)/n; ob=sum(not lost(r) for r in S)/n
    pc=sum(1-r["keep"] for r in S)/n; oc=sum(cause(r)=="cut" for r in S)/n
    pr=sum(r["keep"]*(1-sum(w*s for w,s in zip(r["w"],SH))) for r in S)/n; orr=sum(cause(r) in("other","out") for r in S)/n
    w=[sum(r["w"][i] for r in S)/n for i in range(4)]
    print(f"{lo:>3}-{hi:<3} {n:6d} {ev:6.3f} {ob:6.3f} {100*(ev-ob):+6.1f} | {pc:6.3f} {oc:11.3f} | {pr:11.3f} {orr:9.3f} | "+" ".join(f"{x:.3f}" for x in w))
# per-opponent cut hit rate by gap band and length
print("\npart des adversaires comptés qui touchent le premier, par tranche de distance à la trajectoire (table) et longueur")
G=[0.5,1,2,3,4,6]
n=defaultdict(int);h=defaultdict(int);c=defaultdict(float)
for r in R:
    lb=next(i for i,(lo,hi) in enumerate(LB) if lo<=r["L"]<hi)
    for o in r["opp"]:
        if o["cut"]>0:
            g=next(x for x in G if o["gap"]<x) if o["gap"]<6 else 6
            near=o["along"]<=3
            k=(near,g,lb); n[k]+=1; h[k]+=r.get("first")==o["n"]; c[k]+=o["cut"]
for near in (True,False):
    for g in G:
        row=[]
        for lb in range(len(LB)):
            k=(near,g,lb)
            row.append(f"{h[k]/n[k]:.2f}/{c[k]/n[k]:.2f}({n[k]})" if n[k]>=30 else "   -   ")
        print(("près " if near else "traj ")+f"<{g}: "+"  ".join(row))
