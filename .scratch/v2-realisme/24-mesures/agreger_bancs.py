"""Agrège les bancs 80 contre 70 : indicateur cible par attribut, écart haut-bas et IC95, pour ref / B / A."""
import json, os, sys
S=os.environ.get('BANC24', os.path.dirname(os.path.abspath(__file__)))
TARGET={  # attribut -> indicateurs cibles (clé du relevé 24, ou clé du rapport mesure_v2 "profil haut/bas : ...")
 "Passing":["passes réussies (part)","passes"],
 "First Touch":["contrôles ratés","pertes en conduite"],
 "Technique":["contrôles ratés","passes réussies (part)"],
 "Dribbling":["pertes en conduite","ballons perdus sur tacle"],
 "Tackling":["tacles gagnés","fautes"],
 "Finishing":["buts sur tir","buts moins qualité des tirs"],
 "Decisions":["écart au meilleur choix (moyenne)","passes réussies (part)"],
 "Composure":["passes réussies (part)","contrôles ratés"],
 "Anticipation":["interceptions","tacles gagnés"],
 "Positioning":["interceptions","tirs"],
 "Pace":["course intense par joueur (m)"],
 "Acceleration":["course intense par joueur (m)"],
 "Agility":["pertes en conduite","course intense par joueur (m)"],
 "Strength":["ballons perdus sur tacle","pertes en conduite"],
}
def load(v,a):
    p=f"{S}/bench/{v}/{a}.json"
    if not os.path.exists(p): return None
    return json.load(open(p))
def gap(d,key):
    g=d.get("profil : écart haut - bas par match (IC 95 %)",{})
    if key in g: return g[key]
    h,b=d.get(f"profil haut : {key}"),d.get(f"profil bas : {key}")
    if h is None or b is None: return None
    return {"haut":h,"bas":b,"écart":h-b,"IC95 bas":None,"IC95 haut":None,"significatif":None}
def fmt(x):
    if x is None: return "—"
    s="✔" if x["significatif"] else ("✘" if x["significatif"] is False else "?")
    ci="" if x["IC95 bas"] is None else f" [{x['IC95 bas']:.3g} ; {x['IC95 haut']:.3g}]"
    return f"{x['écart']:+.3g}{ci} {s}"
vs=[v for v in ("ref","B","A") if os.path.isdir(f"{S}/bench/{v}")]
print("| Attribut | Indicateur | "+" | ".join({"ref":"Avant (cubique)","B":"Variante B","A":"Variante A"}[v] for v in vs)+" |")
print("|---|---|"+"---|"*len(vs))
count={v:0 for v in vs}
for a,keys in TARGET.items():
    for i,k in enumerate(keys):
        cells=[]
        for v in vs:
            d=load(v,a); x=gap(d,k) if d else None
            if i==0 and x and x["significatif"]: count[v]+=1
            cells.append(fmt(x))
        print(f"| {a} | {k} | "+" | ".join(cells)+" |")
print("\nAttributs dont l'indicateur principal est significatif :",count)
