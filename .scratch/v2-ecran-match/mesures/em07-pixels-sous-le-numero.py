# Comparaison avec / sans relief : zone du numéro (≤ 0,7 R) identique, bord haut gauche (0,88 R) éclairci.
# Les pixels de la zone centrale recouverts par un autre joueur (relief voisin) sont exclus.
import json, math, sys
from PIL import Image
d = sys.argv[1]
A = Image.open(f"{d}/relief-avec.png").convert("RGB"); B = Image.open(f"{d}/relief-sans.png").convert("RGB")
pts = json.load(open(f"{d}/relief-points.json"))
def covered(x, y, i):
    return any(j != i and (x - q["cx"]) ** 2 + (y - q["cy"]) ** 2 <= (q["R"] + 1.5) ** 2 for j, q in enumerate(pts))
n = diff = 0; edges = []
for i, q in enumerate(pts):
    cx, cy, R = q["cx"], q["cy"], q["R"]
    r = int(0.7 * R)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy > (0.7 * R) ** 2: continue
            x, y = round(cx + dx), round(cy + dy)
            if covered(x, y, i): continue
            n += 1; diff += A.getpixel((x, y)) != B.getpixel((x, y))
    k = 0.88 * R / math.sqrt(2); x, y = round(cx - k), round(cy - k)
    if not covered(x, y, i):
        a, b = A.getpixel((x, y)), B.getpixel((x, y))
        edges.append(sum(a) / 3 - sum(b) / 3)
print(json.dumps({"pixelsZoneNumero": n, "pixelsZoneNumeroDifferents": diff,
                  "bordHautGauche_eclaircissementMoyen_niveaux": round(sum(edges) / len(edges), 1), "bordsMesures": len(edges)}))
