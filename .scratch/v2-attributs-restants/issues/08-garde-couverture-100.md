# 08: Garde de couverture : 100 % des caractéristiques et des 58 gestes branchés

**Fusion du 04/11/2026** (audit de granularité) : la garde du ticket 05 (les 58 gestes préférés tous rattachés à un mécanisme) est la même garde que celle-ci, avec la même liste d'exceptions. Elle est reprise ici. Le ticket 05 reste ouvert : il garde la grille et le branchement mesuré de chaque geste (fréquence, réussite inchangée).

**What to build:** Un test qui liste les colonnes de caractéristiques de `data/joueurs.xlsx` (47 attributs + Taille FM, Weak foot, Pieds, Preferred moves, Postes FM naturels) et échoue si l'une d'elles n'est lue par aucun module de `v2engine/`, sauf si elle figure dans une liste d'exceptions explicite et justifiée. Étend la garde existante `tests/test_v2engine_rayon_attributs.py` plutôt que d'en créer une seconde.

Exceptions attendues au départ (à valider par le propriétaire) : Natural Fitness, **exception assumée et permanente pour un match isolé** (il ne joue qu'entre les matchs, D-V09/D-V10 : il ne pourra s'exprimer qu'une fois la V2 branchée aux compétitions), et chaque attribut dont le ticket porteur n'est pas encore livré, la liste se vidant au fil des tickets 01 à 07 et 09.

**Attributs :** tous.

**Blocked by:** — (posé tout de suite, liste d'exceptions longue au départ).

**Status:** implémenté (14/11/2026) — en attente de /valider-ticket-simulafoot

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée (estimation posée le 14/11/2026 au lancement, le ticket n'en avait pas). Hypothèses : test seul, lecture de la base par `openpyxl`, aucune modification du moteur.
Temps machine, non compté : suite complète (environ 12 min).

**Point de vigilance :** « lu par le moteur » n'est pas « exprimé dans le comportement ». Chaque ticket porteur garde son propre critère mesuré ; cette garde empêche seulement l'oubli.

- [x] Le test échoue si une caractéristique n'est ni lue par `v2engine/` ni dans la liste d'exceptions (`tests/test_v2engine_rayon_attributs.py`, `COVERAGE_EXCEPTIONS` ; 52 caractéristiques, 27 lues, 25 exceptions ; il échoue aussi sur une exception devenue inutile ; échec démontré sur une caractéristique factice)
- [x] Chaque exception cite le ticket qui la lèvera (Natural Fitness : exception permanente pour un match isolé, D-V10)
- [x] Repris du ticket 05 : les 58 valeurs distinctes de `Preferred moves` sont toutes rattachées à un mécanisme et à un ticket porteur (grille du ticket 05) ; le test échoue si une nouvelle valeur apparaît sans rattachement, ou si une paire contradictoire est additionnée au lieu d'être signalée (`PREFERRED_MOVES` : 58 gestes et « (aucun) » ; `CONTRADICTORY_PAIRS` ; une anomalie connue signalée, `KNOWN_CONTRADICTIONS`)
- [x] Suite V2 verte : suite complète 3 035 passés, 0 ignoré, 14 désélectionnés (3 028 + 7 tests ajoutés), 13 min 14 ; fichier exécuté deux fois, 14 passés à chaque fois ; aucun fichier du moteur, V1 ni protégé touché
- [x] Durée réelle relevée, comparée à l'estimation : environ 25 min pour 85 estimées (− 71 %), voir `docs/agents/suivi-estimations.md`

## Comments

**14/11/2026, liste d'exceptions et anomalie validées par le propriétaire** (« ok je valide ») : 25 caractéristiques non lues, chacune avec son ticket (Natural Fitness permanente, D-V10) ; contradiction de la base Nicolò Cambiaghi (Cuts Inside From Both Wings et Hugs Line) inscrite comme anomalie connue, signalée et non corrigée.

**14/11/2026, implémentation.** Garde ajoutée à la fin de `tests/test_v2engine_rayon_attributs.py` (7 tests) : lecture d'un attribut FM par les mêmes lecteurs que le test des rayons ; lecture d'une colonne hors FM (Taille FM, Weak foot, Pieds, Preferred moves, Postes FM naturels) par son champ de `ligue1sim.players.Player` chargé dans `v2engine/`. Base lue avec `openpyxl` (onglet « Infos principales », gestes séparés par « ; »). 3 012 joueurs ont des gestes, 59 valeurs distinctes (58 gestes et « (aucun) »).
