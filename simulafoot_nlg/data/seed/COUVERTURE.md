# Couverture de la banque de commentaire — import du 30/09/2026

> **Cette banque n'est PAS livrable en production. Elle sert à valider le
> moteur de bout en bout (import → sélection → rendu), pas à commenter un
> vrai match.**

## Chiffres

- **281 phrases**, **9 scénarios**, **13 variantes**.
- Couverture estimée : **~33 % des événements d'un match réel** (~100
  événements couverts sur ~300 événements commentables dans un match
  complet — estimation, pas une mesure instrumentée sur un vrai match).

## Scénarios couverts (9)

CARTON_ROUGE, BUT, PENALTY_RATE, COUP_FRANC, CONSTRUCTION, ARRET_GARDIEN,
SITUATION_MATCH, DEBUT_MATCH, GESTE_SIGNATURE.

## Scénarios absents (12) — rien dans la banque

- DÉFENSE (tacle réussi, interception, dégagement)
- CORNER
- FAUTE_SIMPLE (faute non sanctionnée d'un carton)
- TIR_NON_CADRÉ
- HORS-JEU
- REMPLACEMENT
- CARTON_JAUNE
- MI_TEMPS / FIN_MATCH
- STATISTIQUES_PÉRIODIQUES (possession, tirs cumulés à la mi-temps, etc.)
- VAR
- AMBIANCE (hors SITUATION_MATCH — chants, tifos, incidents de tribune)
- BLESSURE

Voir [PLAN_V2_EDITORIAL.md](PLAN_V2_EDITORIAL.md) pour le chiffrage et la
priorisation de ces 12 scénarios.

## Scénarios sous-alimentés (4) — présents mais fragiles à l'usage

| Scénario | Phrases | Cooldown | Risque |
|---|---|---|---|
| CONSTRUCTION | 20 | 2 matchs | Phase la plus fréquente d'un match réel (dizaines d'occurrences/match) contre seulement 20 gabarits — épuisement du pool probable dès la 1ʳᵉ mi-temps d'un match simulé. |
| ARRET_GARDIEN | 38 | 2 matchs | Fréquence élevée (plusieurs arrêts/match), pool le plus large des sous-alimentés mais encore court face à un cooldown de seulement 2 matchs. |
| SITUATION_MATCH | 30 | 1 match | Cooldown le plus court du lot (par design, voir justification dans `convert_commentary_xlsx_to_yaml.py`) — un pool de 30 phrases avec un cooldown de 1 match s'épuise vite sur un match à commentaire dense. |
| COUP_FRANC | 20 | 3 matchs | Pool le plus petit des scénarios "action" restants ; 35 % de redondance structurelle corrigée à 10 % lors de l'audit du 30/09/2026, mais la taille du pool reste limitante. |

## Pourquoi importer quand même

Décision assumée (30/09/2026) : importer une banque partielle permet de
faire tourner le pipeline (scenario_engine → conditions → sélection → rendu,
une fois ces deux derniers implémentés) et de découvrir en pratique ce qui
manque, plutôt que de le théoriser indéfiniment avant tout import. Voir le
smoke test du même jour pour ce que ça a révélé concrètement.

## Ne pas confondre avec une banque complète

Dans trois mois, sans ce fichier : 281 phrases importées et un moteur qui
tourne peuvent donner l'illusion d'un système fini. Ce n'est pas le cas —
voir la clause en tête de document.
