"""Tolérance 02a2 : bruit = 1,96·√(sA²/nA + sB²/nB), écart-type par match des séries de référence A (graines 0-49) et
B (50-99) de 02a1 ; écart jugé = moyenne(02a2-après-A) − moyenne(02a1-après2-A), mêmes graines."""
import json, math, statistics as st, sys
L=lambda p: json.load(open(p))['par match']
A,B,AV,AP=L('02a1-ref-A.json'),L('02a1-ref-B.json'),L('02a1-apres2-A.json'),L('02a2-apres-A.json')
def vals(s,k): return [v for v in s.get(k,[]) if v is not None]
rows=[]; ab=0
for k in sorted(A.keys()&B.keys()&AV.keys()&AP.keys()):
    a,b,av,ap=vals(A,k),vals(B,k),vals(AV,k),vals(AP,k)
    if min(len(a),len(b),len(av),len(ap))<2: continue
    noise=1.96*math.sqrt(st.variance(a)/len(a)+st.variance(b)/len(b))
    dab=st.fmean(b)-st.fmean(a); d=st.fmean(ap)-st.fmean(av)
    r=abs(d)/noise if noise>0 else (0 if d==0 else math.inf)
    rows.append((r,k,st.fmean(av),st.fmean(ap),d,noise)); ab+= noise>0 and abs(dab)>noise
n=len(rows); out=sum(r>1 for r,*_ in rows)
print(f"indicateurs comparés : {n}\nA contre B hors bruit : {ab} ({100*ab/n:.1f}%)\n02a2 contre 02a1 hors bruit : {out} ({100*out/n:.1f}%)")
pat=sys.argv[1:] 
print("\n-- issues et tirs --")
for r,k,x,y,d,no in sorted(rows,key=lambda t:t[1]):
    if any(p in k for p in pat) and 'tranche' not in k: print(f"{k} : avant {x:.4g} | après {y:.4g} | écart {d:+.4g} | bruit ±{no:.3g} | {r:.1f}×")
print("\n-- 25 plus gros écarts --")
for r,k,x,y,d,no in sorted(rows,reverse=True)[:25]: print(f"{r:.1f}× {k} : {x:.4g} -> {y:.4g} (±{no:.3g})")
