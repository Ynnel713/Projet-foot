"""Tolérance 03a (méthode du 02a1, 02c) : bruit = séries de référence A/B du 02a1 ; écart = moyenne(03a-apres) − moyenne(03a-avant), graines 0-49, même moteur hors 03a (avant : code de 145a292). Usage, depuis ce dossier : python 03a-tolerance.py [motifs...]"""
import json, math, statistics as st, sys
H=''
L=lambda p: json.load(open(p))['par match']
A,B,AV,AP=L(H+'02a1-ref-A.json'),L(H+'02a1-ref-B.json'),L('03a-avant.json'),L('03a-apres.json')
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
print(f"indicateurs comparés : {n}\nA contre B hors bruit : {ab} ({100*ab/n:.1f}%)\n03a contre avant hors bruit : {out} ({100*out/n:.1f}%)")
for sec in ('avant','apres'):
    s=json.load(open({'avant':'03a-avant.json','apres':'03a-apres.json'}[sec]))['secondes par match']; print(f"secondes par match {sec} : {st.fmean(s) if isinstance(s,list) else s}")
print("\n-- indicateurs choisis --")
for r,k,x,y,d,no in sorted(rows,key=lambda t:t[1]):
    if any(p in k for p in sys.argv[1:]) and 'tranche' not in k and 'poste' not in k:
        print(f"{k} : avant {x:.4g} | après {y:.4g} | écart {d:+.4g} | bruit ±{no:.3g} | {r:.1f}×")
print("\n-- 30 plus gros écarts --")
for r,k,x,y,d,no in sorted(rows,reverse=True)[:30]: print(f"{r:.1f}× {k} : {x:.4g} -> {y:.4g} (±{no:.3g})")
