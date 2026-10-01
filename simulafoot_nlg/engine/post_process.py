"""SQUELETTE -- post-traitement linguistique du texte rendu par
template_filler.render (accords, elision, ponctuation). Aucune
implementation dans cette session.

Algorithme prevu :
    1. Elision : "le Ailier" -> "l'Ailier", "de Arsenal" -> "d'Arsenal" --
       regle sur voyelle/h initial du mot suivant, table d'exceptions pour
       les "h aspire" francais courants dans des noms de club/joueur.
    2. Majuscule initiale de phrase (le gabarit peut commencer par un slot en
       minuscule, ex. "{player_name} ...").
    3. Ponctuation : une seule marque finale (pas de "!." ni ".." issus d'un
       slot qui se termine deja par une ponctuation + le texte du gabarit qui
       en ajoute une autre), espace insecable avant ; : ! ? si un jour une
       sortie typographique francaise stricte est visee (a confirmer).
    4. Espaces multiples ecrases en un seul (un slot vide au milieu d'un
       gabarit laisse souvent un double espace).
    Chaque regle doit etre une fonction pure testable isolement (voir
    tests/test_post_process.py : elision, majuscule, ponctuation, double
    espace comme 4 cas distincts) plutot qu'un unique bloc regex monolithique.
"""

from __future__ import annotations

import re

_ESPACES_MULTIPLES_RE = re.compile(r"[ 	]{2,}")
_PONCTUATION_FINALE_RE = re.compile(r"([.!?…]+)(\s*)$")
# Series de marques finales a CONSERVER telles quelles : points de suspension et
# combinaisons expressives ("?!" / "!?" sont voulues, pas des collisions).
_SERIES_VOULUES = frozenset({"...", "…", "?!", "!?"})


def ecraser_espaces(text: str) -> str:
    """Espaces et tabulations consecutifs -> un seul espace, et aucun en debut ni
    en fin de texte (un slot vide laisse un double espace au milieu d'un gabarit,
    ou un espace en tete). L'espace insecable (U+00A0, typographie francaise) et
    les retours a la ligne ne sont jamais touches."""
    return _ESPACES_MULTIPLES_RE.sub(" ", text).strip(" 	")


def ponctuation_finale(text: str) -> str:
    """Une seule marque finale. Un slot qui se termine deja par une ponctuation, suivi
    d'un gabarit qui en ajoute une autre, laisse "!." ou ".." : la serie finale est
    ramenee a UNE marque (le plus expressif l'emporte : "?!" > "!" > "?" > "..." > ".").
    Conserves tels quels : "...", "…", "?!" et "!?". Un texte sans ponctuation finale
    n'en recoit pas (ce n'est pas le role de cette regle). Les espaces apres la
    marque, et l'espace avant elle ("Quel but !"), ne sont pas touches."""
    correspondance = _PONCTUATION_FINALE_RE.search(text)
    if correspondance is None:
        return text
    serie, espaces = correspondance.group(1), correspondance.group(2)
    if serie in _SERIES_VOULUES:
        return text
    if "?" in serie and "!" in serie:
        marque = "?!"
    elif "!" in serie:
        marque = "!"
    elif "?" in serie:
        marque = "?"
    elif "…" in serie:
        marque = "…"
    else:
        marque = "."
    return text[: correspondance.start()] + marque + espaces


def majuscule_initiale(text: str) -> str:
    """Met en majuscule la premiere LETTRE du texte (un gabarit peut commencer par
    un slot en minuscule : "mbappe marque" -> "Mbappe marque"). Les signes d'ouverture
    (guillemets, tirets, espaces) sont sautes ; le reste du texte n'est pas touche.
    Si le premier caractere alphanumerique est un chiffre ("3 joueurs..."), rien ne
    change : on ne cherche pas une lettre plus loin dans la phrase."""
    for position, caractere in enumerate(text):
        if caractere.isalpha():
            return text[:position] + caractere.upper() + text[position + 1 :]
        if caractere.isalnum():
            return text
    return text


def apply(text: str) -> str:
    """Applique le post-traitement linguistique complet a `text` (deja
    entierement rendu par template_filler.render, tous les slots resolus).
    Voir algorithme prevu en tete de module. Leve NotImplementedError tant
    que la banque de phrases n'est pas livree."""
    raise NotImplementedError(
        "post_process.apply : squelette non implémenté -- voir la docstring "
        "de engine/post_process.py pour l'algorithme prévu."
    )
