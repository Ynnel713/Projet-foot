"""Contrôle de l'ordre de réalisation (ticket 18j) : chaque prérequis déclaré (« Blocked by ») d'un ticket de l'ordre est
livré, ou placé plus tôt dans l'ordre. Lit la fin de la P0 et les blocs 1 à 6 de la Vague 2 dans spec.md."""
import glob, re, sys
ROOT = ".scratch"
def path(ch, tid):
    m = glob.glob(f"{ROOT}/{ch}/issues/{tid}-*.md")
    return m[0] if m else None
def delivered(ch, tid):
    p = path(ch, tid)
    if p is None: return None
    st = next((l for l in open(p, encoding="utf-8") if re.match(r"\*\*Status ?:\*\*", l)), "")
    return "livré" in st or "resolved" in st
spec = open(f"{ROOT}/v2-realisme/spec.md", encoding="utf-8").read()
lines = [l for l in spec.splitlines() if l.startswith("   - **Fin de la P0") or re.match(r"   - \*\*Bloc [1-6]", l)]
order = []
for l in lines:
    body = l.split(":", 1)[1] if "** :" in l else l
    body = l[l.index("** :") + 4:] if "** :" in l else l
    current = "v2-realisme"
    for m in re.finditer(r"`(v2-[a-z-]+)/([0-9]+[a-z]?)`|`([0-9]+[a-z]?)`|\b([0-9]{2}[a-z]?)\b", body):
        if m.group(1): current = m.group(1); order.append((current, m.group(2)))
        elif m.group(3): order.append((current, m.group(3)))
        else: current = "v2-realisme"; order.append((current, m.group(4)))
seen, bad = set(), []
for ch, tid in order:
    p = path(ch, tid)
    if p is None: bad.append(f"{ch}/{tid} : fichier introuvable"); continue
    blk = next((l for l in open(p, encoding="utf-8") if re.search(r"Blocked by", l, re.I)), "")
    blk = blk.split(":", 1)[1] if ":" in blk else ""
    blk = re.sub(r"\([^)]*\)", "", blk)  # titres entre parenthèses
    blk = re.sub(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", "", blk)  # dates
    blk = blk.split("À livrer avec")[0]  # livraison conjointe : pas une dépendance
    deps, cur = [], ch
    for m in re.finditer(r"`(v2-[a-z-]+)/([0-9]+[a-z]?)`|`([0-9]+[a-z]?)`|(v2-[a-z-]+)/([0-9]+[a-z]?)|\b([0-9]{2}[a-z]?)\b", blk):
        if m.group(1): cur = m.group(1); deps.append((cur, m.group(2)))
        elif m.group(3): deps.append((cur, m.group(3)))
        elif m.group(4): deps.append((m.group(4), m.group(5)))
        else: cur = ch; deps.append((ch, m.group(6)))
    for d in deps:
        if d in seen: continue
        st = delivered(*d)
        if st is None: bad.append(f"{ch}/{tid} : prérequis {d[0]}/{d[1]} introuvable"); continue
        if not st: bad.append(f"{ch}/{tid} : prérequis {d[0]}/{d[1]} ni livré ni placé avant")
    seen.add((ch, tid))
print(f"tickets dans l'ordre : {len(order)}")
print("\n".join(bad) if bad else "AUCUNE VIOLATION : chaque prérequis est livré ou placé avant")
