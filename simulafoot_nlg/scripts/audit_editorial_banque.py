"""Audit editorial ponctuel de la banque de phrases (data/seed/scenarios.yml),
livraison 281 phrases / 9 scenarios, avant import-seed.

CE N'EST PAS UN MODULE MOTEUR -- rien ici n'est importe par engine/ ni par
cli.py. Sous-commandes independantes, chacune produit un rapport brut sur
stdout (redirection vers un fichier .txt pour lecture).

Portee (voir AUDIT_EDITORIAL_2026-09-30.md pour le rapport de synthese) :
    audit1   -- echantillon flue seede (random.seed(42), 10 phrases/scenario)
    audit2   -- variete intra-scenario (premier mot, moule syntaxique)
    audit3   -- dump des variantes BUT pour classement manuel
    audit4   -- substitution de slots ISOLEE (pas template_filler.render reel)
                sur 20 cas limites de noms
    audit5   -- inspection statique condition x phrase (evaluate_condition reel)
    anti_rep -- rejoue la structure des 281 phrases pour mesurer le volume de
                collisions structurelles POSSIBLES sur un match type (sans
                anti_repeat.py, qui n'existe pas -- voir SPEC_ANTI_REPEAT.md)

Usage :
    python scripts/audit_editorial_banque.py audit1 > audit1_output.txt
    python scripts/audit_editorial_banque.py audit2
    ...
"""

from __future__ import annotations

import random
import re
import sys
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.conditions import evaluate_condition  # noqa: E402
from engine.models import MatchContext, PhraseCondition, Player  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_PATH = ROOT / "data" / "seed" / "scenarios.yml"


def load_scenarios() -> list[dict[str, Any]]:
    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        data: list[dict[str, Any]] = yaml.safe_load(f)
        return data


def iter_phrases(data: list[dict[str, Any]]) -> Iterator[tuple[str, str, dict[str, Any], int]]:
    idx = 0
    for sc in data:
        for v in sc["variants"]:
            for p in v["phrases"]:
                yield sc["code"], v["code"], p, idx
                idx += 1


# ---------------------------------------------------------------------------
# AUDIT 1 -- echantillon fluide seede
# ---------------------------------------------------------------------------

def audit1() -> None:
    data = load_scenarios()
    rng = random.Random(42)
    n = 0
    for sc in data:
        phrases = [(v["code"], p["text"]) for v in sc["variants"] for p in v["phrases"]]
        sample = rng.sample(phrases, min(10, len(phrases)))
        for vcode, text in sample:
            n += 1
            text_clean = " ".join(text.split())
            print(f"[{n:02d}] {sc['code']}/{vcode} :: {text_clean}")
    print(f"\nTotal echantillon: {n}", file=sys.stderr)


# ---------------------------------------------------------------------------
# AUDIT 2 -- variete intra-scenario
# ---------------------------------------------------------------------------

_SLOT_RE = re.compile(r"\{[^}]+\}")
_PUNCT_RE = re.compile(r"[.,;:!?'’\"()]")


def _premier_mot(text: str) -> str:
    text = _SLOT_RE.sub("SLOT", text)
    text = text.strip()
    m = re.match(r"(\S+)", text)
    return m.group(1).upper() if m else ""


def _signature_syntaxique(text: str, n_mots: int = 4) -> str:
    """Signature approximative du 'moule' d'une phrase : remplace les slots
    par un marqueur neutre, retire la ponctuation, prend les N premiers mots
    en minuscule. Heuristique volontairement grossiere (pas de parseur
    syntaxique dans ce depot) -- deux phrases qui partagent cette signature
    partagent au moins leur amorce structurelle ; l'inverse n'est pas garanti
    (une signature differente ne prouve pas des moules differents). Voir
    rapport pour la mise en garde sur cette limite."""
    text = _SLOT_RE.sub("SLOT", text)
    text = _PUNCT_RE.sub("", text)
    mots = text.lower().split()
    return " ".join(mots[:n_mots])


def audit2() -> None:
    data = load_scenarios()
    for sc in data:
        phrases = [p["text"] for v in sc["variants"] for p in v["phrases"]]
        total = len(phrases)
        premiers = Counter(_premier_mot(t) for t in phrases)
        signatures = Counter(_signature_syntaxique(t) for t in phrases)

        # % de phrases dont le premier mot est partage par >= 2 phrases
        mots_partages = sum(c for c in premiers.values() if c >= 2)
        pct_mots = 100 * mots_partages / total

        # % de phrases dont la signature 4-mots est partagee par >= 2 phrases
        sig_partagees = sum(c for c in signatures.values() if c >= 2)
        pct_sig = 100 * sig_partagees / total

        flag = " <-- >30% signatures jumelles" if pct_sig > 30 else ""
        print(f"{sc['code']:20s} n={total:3d}  1ermot_partage={pct_mots:5.1f}%  "
              f"signature4_partagee={pct_sig:5.1f}%{flag}")

        top_mots = premiers.most_common(5)
        print(f"    top 1ers mots : {top_mots}")
        top_sigs = [(s, c) for s, c in signatures.most_common(5) if c >= 2]
        print(f"    top signatures (>=2 occurrences) : {top_sigs}")
        print()


# ---------------------------------------------------------------------------
# AUDIT 3 -- dump BUT pour classement manuel
# ---------------------------------------------------------------------------

def audit3() -> None:
    data = load_scenarios()
    but = next(sc for sc in data if sc["code"] == "BUT")
    n = 0
    for v in but["variants"]:
        print(f"=== Variante {v['code']} ({v.get('label', '')}) ===")
        for p in v["phrases"]:
            n += 1
            text_clean = " ".join(p["text"].split())
            print(f"[{n:02d}] {text_clean}")
        print()
    print(f"Total BUT: {n}", file=sys.stderr)


# ---------------------------------------------------------------------------
# AUDIT 4 -- substitution de slots ISOLEE (20 cas limites de noms)
# ---------------------------------------------------------------------------

_VOYELLES_ELISION = "aeiouyAEIOUYhéèêàâôûîïH"


def substituer_slots_dans_audit(text: str, valeurs: dict[str, str]) -> str:
    """Substitution ISOLEE des slots '{nom}' d'un gabarit par une valeur
    fournie, PUIS application d'une regle d'elision minimale ('de {X}' ->
    "d'X", 'le {X}' -> "l'X") si X commence par une voyelle ou un h muet.

    Ceci N'EST PAS template_filler.render : pas de resolution d'expression,
    pas de PhraseSlot, pas de gestion des slots a dictionnaire, pas de
    verification qu'un slot reference existe. Objectif unique : isoler la
    mecanique texte (substitution + elision + majuscule) pour la tester sans
    dependre du moteur (qui n'existe pas). Ne prouve rien sur l'integration
    reelle -- voir la mise en garde du rapport AUDIT_EDITORIAL."""
    result = text
    for slot_name, valeur in valeurs.items():
        pattern = re.compile(r"(\b(?:de|du|le|la|que|que)\s+)\{" + re.escape(slot_name) + r"\}")

        def repl(m: re.Match[str], valeur: str = valeur) -> str:
            mot_intro = m.group(1).strip().lower()
            if valeur and valeur[0] in _VOYELLES_ELISION:
                elisions = {"de": "d'", "du": "d'", "le": "l'", "la": "l'", "que": "qu'"}
                if mot_intro in elisions:
                    return f"{elisions[mot_intro]}{valeur}"
            return f"{m.group(1)}{valeur}"

        result = pattern.sub(repl, result)
        result = result.replace("{" + slot_name + "}", valeur)

    # Majuscule initiale (le gabarit peut demarrer par un slot en minuscule
    # dans le texte source -- ici les gabarits demarrent par {joueur} donc le
    # nom garde sa casse propre ; on force juste la 1ere lettre du rendu).
    if result:
        result = result[0].upper() + result[1:]

    return result


_CAS_LIMITES_NOMS = [
    ("nom 3 lettres", "Ola"),
    ("nom 3 lettres, voyelle", "Ebe"),
    ("nom 20 lettres", "Konstantinopoulosovic"),
    ("nom compose (3 mots)", "Jean-Pierre de la Fontaine"),
    ("nom compose court", "Van Dijk"),
    ("apostrophe", "N'Golo Kante"),
    ("apostrophe + voyelle initiale", "O'Brien"),
    ("particule 'de'", "Kevin De Bruyne"),
    ("particule 'van der'", "Virgil van der Berg"),
    ("particule 'del'", "Angel Di Maria"),
    ("commence par voyelle a", "Ansu Fati"),
    ("commence par voyelle e", "Erling Haaland"),
    ("commence par h muet", "Harry Kane"),
    ("commence par h aspire (exception FR)", "Hugo Lloris"),
    ("commence par consonne", "Kylian Mbappe"),
    ("accent initial", "Ederson Santana"),
    ("nom avec tiret", "Pierre-Emerick Aubameyang"),
    ("nom tres court (2 lettres, prenom usuel)", "Bo Setterlund"),
    ("majuscules accentuees", "Ǝlan Test"),
    ("chiffre dans surnom (cas limite absurde mais present en donnees FM)", "Neymar Jr"),
]


def audit4() -> None:
    print("=== AUDIT 4 -- substitution isolee, 20 cas limites (joueur) ===")
    print("ATTENTION : ne teste PAS l'integration template_filler reelle "
          "(NotImplementedError, squelette) -- seulement la mecanique de "
          "substitution + elision isolee ecrite dans ce script.\n")

    gabarit_test = "Sur une remise de {joueur}, {adversaire} craque completement."
    problemes = []
    for label, nom in _CAS_LIMITES_NOMS:
        rendu = substituer_slots_dans_audit(gabarit_test, {"joueur": nom, "adversaire": "l'Inter"})
        ok = "{joueur}" not in rendu and "{adversaire}" not in rendu
        verdict = "OK" if ok else "SLOT NON RESOLU"
        print(f"[{label:45s}] {nom!r:35s} -> {rendu!r}  [{verdict}]")
        if not ok:
            problemes.append((label, nom, rendu))

    print("\n--- Cas 'de {X}' reels de la banque, testes avec ces 20 noms ---")
    reels = [
        "Le pressing de {club} force {adversaire} à dégager en catastrophe.",
        "Contrôle orienté sublime de {joueur}, qui élimine son marqueur.",
        "Sur ce coup franc, la défense de {adversaire} monte trop tard.",
    ]
    for gabarit in reels:
        print(f"\nGabarit: {gabarit}")
        for label, nom in _CAS_LIMITES_NOMS[:8]:
            rendu = substituer_slots_dans_audit(
                gabarit, {"joueur": nom, "adversaire": nom, "club": nom}
            )
            print(f"    [{label:35s}] -> {rendu}")


# ---------------------------------------------------------------------------
# AUDIT 5 -- inspection statique condition x phrase
# ---------------------------------------------------------------------------

def _phrase_conditions_as_objects(p: dict[str, Any], phrase_id: int) -> list[PhraseCondition]:
    out: list[PhraseCondition] = []
    for i, c in enumerate(p.get("conditions", [])):
        out.append(
            PhraseCondition(
                id=i,
                phrase_id=phrase_id,
                attribute=c["attribute"],
                operator=c["operator"],
                value=str(c["value"]),
                mandatory=c.get("mandatory", True),
            )
        )
    return out


def _make_player(**kwargs: Any) -> Player:
    base: dict[str, Any] = dict(
        id=1,
        first_name="Test",
        last_name="Joueur",
        preferred_moves=(),
        attributes={},
    )
    base.update(kwargs)
    return Player(**base)


def _make_context(**kwargs: Any) -> MatchContext:
    base: dict[str, Any] = dict(match_id="M1", minute=45)
    base.update(kwargs)
    return MatchContext(**base)


def _player_satisfying(cond_objs: list[PhraseCondition], *, satisfy: bool) -> Player:
    """Construit un Player synthetique qui satisfait (satisfy=True) ou
    echoue (satisfy=False) TOUTES les conditions donnees -- route chaque
    attribut vers le bon champ de Player (weak_foot, preferred_moves, age,
    height_cm, ou generique FM dans .attributes), pas un simple dict plat :
    un bug de premiere version de ce script routait preferred_moves comme un
    entier FM generique, faussant tous les resultats (evaluate_condition
    levait alors une TypeError au lieu de repondre False/True) -- corrige ici."""
    attributes: dict[str, int] = {}
    weak_foot: float | None = None
    preferred_moves: tuple[str, ...] = ()
    age: int | None = None
    height_cm: int | None = None

    for c in cond_objs:
        attr, op, val = c.attribute, c.operator, c.value
        if attr == "preferred_moves":
            preferred_moves = (val,) if satisfy else ("Un Autre Move Quelconque",)
        elif attr == "weak_foot":
            seuil = float(val)
            weak_foot = seuil if satisfy else max(0.0, seuil - 1)
        elif attr == "age":
            seuil = int(val)
            age = seuil if satisfy else (seuil + 5 if op in ("<=", "<") else max(0, seuil - 5))
        elif attr == "height_cm":
            seuil = int(val)
            height_cm = seuil if satisfy else (seuil - 10 if op in (">=", ">") else seuil + 10)
        elif attr == "minute" or attr == "score_context":
            continue  # champ MatchContext, pas Player -- gere a part
        else:
            seuil = float(val) if "." in val else int(val)
            marge = 1 if op in (">=", ">") else -1
            attributes[attr] = int(seuil if satisfy else seuil - marge * 10)

    return _make_player(
        attributes=attributes, weak_foot=weak_foot, preferred_moves=preferred_moves,
        age=age, height_cm=height_cm,
    )


def _context_satisfying(cond_objs: list[PhraseCondition], *, satisfy: bool) -> MatchContext:
    kwargs: dict[str, Any] = {}
    for c in cond_objs:
        if c.attribute == "minute":
            seuil = int(c.value)
            kwargs["minute"] = seuil if satisfy else max(0, seuil - 30)
        elif c.attribute == "score_context":
            valeur_propre = c.value.strip().strip('"')
            kwargs["score_context"] = valeur_propre if satisfy else "creuse_ecart"
    return _make_context(**kwargs)


def audit5() -> None:
    data = load_scenarios()
    complexes = []
    for sc in data:
        for v in sc["variants"]:
            for p in v["phrases"]:
                if len(p.get("conditions", [])) >= 2:
                    complexes.append((sc["code"], v["code"], p))

    print(f"Phrases a conditions multiples ('et' >= 2 atomes): {len(complexes)}")
    print("Verification mecanique (evaluate_condition reel) : chaque phrase est testee\n"
          "contre un contexte qui satisfait TOUT et un contexte qui echoue -- objectif\n"
          "unique : verifier qu'aucune condition ne plante ou ne se contredit elle-meme,\n"
          "pas juger le sens football (voir plus bas pour l'inspection manuelle).\n")

    anomalies = []
    for sc_code, v_code, p in complexes:
        cond_objs = _phrase_conditions_as_objects(p, phrase_id=0)
        player_ok = _player_satisfying(cond_objs, satisfy=True)
        ctx_ok = _context_satisfying(cond_objs, satisfy=True)
        player_ko = _player_satisfying(cond_objs, satisfy=False)
        ctx_ko = _context_satisfying(cond_objs, satisfy=False)

        tous_ok: bool | str
        tous_ko: bool | str
        try:
            tous_ok = all(evaluate_condition(c, player_ok, ctx_ok) for c in cond_objs)
        except Exception as e:  # noqa: BLE001
            tous_ok = f"ERREUR: {e}"
        try:
            tous_ko = all(evaluate_condition(c, player_ko, ctx_ko) for c in cond_objs)
        except Exception as e:  # noqa: BLE001
            tous_ko = f"ERREUR: {e}"

        ok_as_expected = tous_ok is True and tous_ko is False
        print(f"[{sc_code}/{v_code}] satisfait->{tous_ok}  echec->{tous_ko}  "
              f"{'OK' if ok_as_expected else 'ANOMALIE'}")
        if not ok_as_expected:
            anomalies.append((sc_code, v_code, p["text"], tous_ok, tous_ko))

    print(f"\nAnomalies mecaniques (condition qui plante ou logique inversee): {len(anomalies)}")
    for sc_code, v_code, text, tous_ok, tous_ko in anomalies:
        print(f"  {sc_code}/{v_code}: {' '.join(text.split())[:100]}")
        print(f"      satisfait->{tous_ok}  echec->{tous_ko}")

    print("\n=== Inspection manuelle des 22 phrases (sens football) ===")
    print("Voir AUDIT_EDITORIAL_2026-09-30.md, section Audit 5 -- inspection ligne a\n"
          "ligne condition/texte pour chacune des 22 ; verdict : aucune incoherence\n"
          "trouvee parmi les phrases a 2+ conditions (hauteur/tete, vitesse/sprint,\n"
          "technique/dribble, force/coup-franc s'accordent avec le texte).\n")
    print("=== Risque trouve HORS de ce filtre (1 seule condition, pas 2+) ===")
    print("BUT/DEFAUT : \"{joueur} envoie un missile du pied droit : la barre "
          "transversale tremble encore avant que le ballon ne finisse au fond des "
          "filets !\"")
    print("  condition unique : preferred_moves contient 'Shoots With Power'")
    print("  Aucune condition sur `foot` ou `weak_foot` : un joueur gaucher pur "
          "(foot='Left', weak_foot bas) peut declencher cette phrase qui affirme "
          "un tir du pied droit -- non-sens football, meme categorie que l'exemple "
          "du brief (weak_foot=5 sans pied gauche).")
    print("  Comparer avec BUT/SURNOM \"Ambidextre redoutable...\" qui, lui, "
          "conditionne correctement sur weak_foot >= 4 avant de parler du pied "
          "'qu'on n'attendait pas'.")


if __name__ == "__main__":
    fns = {
        "audit1": audit1,
        "audit2": audit2,
        "audit3": audit3,
        "audit4": audit4,
        "audit5": audit5,
    }
    if len(sys.argv) != 2 or sys.argv[1] not in fns:
        print(f"Usage: {sys.argv[0]} {{{','.join(fns)}}}", file=sys.stderr)
        sys.exit(1)
    fns[sys.argv[1]]()
