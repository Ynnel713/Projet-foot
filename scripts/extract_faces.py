"""
Extrait les photos de joueurs du megapack Sortitoutsi (cutout) pour les
joueurs déjà enrichis FM26 dans data/joueurs.xlsx, vers assets/faces/.

Principe
--------
Le megapack (un .rar, ex. sortitoutsi_cutout_megapack_2026.09.rar,
téléchargé séparément -- ~16 Go, jamais versionné) contient un PNG par
joueur nommé sortitoutsi/faces/face_<ID Sortitoutsi>.png. fminside.net et
Sortitoutsi partagent la même base de données FM : l'ID Sortitoutsi EST le
nombre dans la "FMInside URL" déjà en base (ex.
.../14229525-enzo-fernandez -> 14229525) -- aucune conversion à deviner.

Chaque photo trouvée est copiée dans assets/faces/<ID Excel>.png (renommée
par l'ID Excel, pas l'ID Sortitoutsi, pour que le reste de l'appli -- voir
ligue1sim.faces.face_path -- n'ait jamais besoin de connaître l'URL fminside
d'un joueur). Incrémental : une photo déjà extraite n'est jamais retéléchargée.

Installation : 7-Zip doit être sur le PATH (commande `7z`).

Exemple
-------
    python scripts/extract_faces.py --archive "C:\\...\\sortitoutsi_cutout_megapack_2026.09.rar"
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import openpyxl

SHEET = "Infos principales"
ID_COL = "ID"
URL_COL = "FMInside URL"
ARCHIVE_ENTRY_PREFIX = "sortitoutsi/faces/face_"
# Le "." final capture l'ID meme quand le slug de nom contient des chiffres
# (ex. "...-mbappe-2") -- l'ID est toujours le PREMIER groupe de chiffres
# juste apres le dernier "/".
UID_RE = re.compile(r"/(\d+)-[^/]+/?$")


def load_id_to_uid(xlsx: Path) -> dict[int, str]:
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb[SHEET]
    headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    idx = {h: i for i, h in enumerate(headers)}
    if ID_COL not in idx or URL_COL not in idx:
        sys.exit(f"Colonnes introuvables dans '{SHEET}' : {ID_COL!r} / {URL_COL!r}")
    out: dict[int, str] = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        eid, url = row[idx[ID_COL]], row[idx[URL_COL]]
        if eid is None or not url:
            continue
        m = UID_RE.search(str(url))
        if m:
            out[int(eid)] = m.group(1)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive", type=Path, required=True, help="Chemin du .rar du megapack")
    ap.add_argument("--excel", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "joueurs.xlsx")
    ap.add_argument("--dest", type=Path, default=Path(__file__).resolve().parent.parent / "assets" / "faces")
    args = ap.parse_args()

    if not args.archive.is_file():
        sys.exit(f"Archive introuvable : {args.archive}")

    id_to_uid = load_id_to_uid(args.excel)
    print(f"{len(id_to_uid)} joueurs avec une FMInside URL dans {args.excel.name}")

    args.dest.mkdir(parents=True, exist_ok=True)
    todo = {eid: uid for eid, uid in id_to_uid.items() if not (args.dest / f"{eid}.png").exists()}
    print(f"{len(todo)} photos à extraire ({len(id_to_uid) - len(todo)} déjà présentes)")
    if not todo:
        return

    # Par lots (pas un seul appel 7z avec tous les noms) : la ligne de
    # commande Windows a une limite de longueur -- au-delà d'un millier de
    # joueurs, un seul appel dépasse cette limite ("Nom de fichier ou
    # extension trop long", trouvé en le lançant sur les 3381 joueurs déjà
    # enrichis). Toujours moins d'appels qu'un 7z par joueur, qui resterait
    # coûteux sur un .rar de ~16 Go.
    BATCH_SIZE = 200
    items = list(todo.items())
    found, missing = 0, []
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        for i in range(0, len(items), BATCH_SIZE):
            batch = items[i : i + BATCH_SIZE]
            wanted = [f"{ARCHIVE_ENTRY_PREFIX}{uid}.png" for _eid, uid in batch]
            cmd = ["7z", "e", str(args.archive), f"-o{tmp}", "-y", *wanted]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                sys.exit(f"7z a échoué (code {result.returncode}) sur le lot {i}-{i + len(batch)} :\n"
                          f"{result.stderr or result.stdout}")
            for eid, uid in batch:
                src = tmp / f"face_{uid}.png"
                if src.exists():
                    shutil.copy2(src, args.dest / f"{eid}.png")
                    src.unlink()
                    found += 1
                else:
                    missing.append(eid)
            print(f"  lot {i // BATCH_SIZE + 1}/{(len(items) - 1) // BATCH_SIZE + 1} : "
                  f"{found} trouvées jusqu'ici")

    print(f"{found} photos extraites dans {args.dest}")
    if missing:
        preview = missing[:20]
        suffix = f" (+{len(missing) - 20} autres)" if len(missing) > 20 else ""
        print(f"{len(missing)} introuvables dans le megapack (ID Excel) : {preview}{suffix}")


if __name__ == "__main__":
    main()
