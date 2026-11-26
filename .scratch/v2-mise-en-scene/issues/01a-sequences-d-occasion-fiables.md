# 01a: Séquences d'occasion fiables (réserves A1 et A2 du `v2-collectif/28c`)

**Chantier :** `v2-mise-en-scene` (audit du mode « moments clés », 26/11/2026). **Catégorie :** instrumentation de la trace.

**Exception accordée par le propriétaire (26/11/2026) :** ce ticket modifie `v2engine/occasion.py` et l'étiquette d'origine écrite dans la trace par `v2engine/match.py` (`_received_as`, `_shot_origin`, `_danger_origin` ; `ball.came_from` ne sert qu'à construire cette étiquette). Conditions, toutes vérifiées à la clôture :
- **lecture seule** : aucun tirage, aucune donnée lue par une décision, un mouvement ou une résolution ;
- **jeu inchangé** : à graine fixée, positions, ballon, buts, tirs (hors champ `origin`) et événements du journal identiques avant et après ;
- **seule la trace change** : `MatchTrace.chances` (découpage des séquences, champ `origin`), `ShotEvent.origin` et `ReceptionEvent.origin` (même étiquette, produite par `_received_as`).

**Constat vérifié (26/11/2026) :**
- `ChanceTracker.update` (`occasion.py`) ferme une séquence au premier pas où le danger passe sous `SEQUENCE_FLOOR` (0,10) : une même action qui oscille autour du plancher est coupée en deux grosses occasions (réserve A1). Pour les modes, c'est un doublon garanti.
- L'origine « récupération » mélange le ballon gagné sur l'adversaire et le ballon perdu par l'attaque elle-même (réserve A2) ; elle sert à classer les actions de contre-attaque au `01b`.
- `trace.chances` n'est lu nulle part dans `v2engine/` hors `occasion.py` (vérifié par recherche) ; `ShotEvent.origin` n'est lu par aucune résolution (les `.origin` de `match.py` lignes 448 à 945 sont la position de départ du tir en vol, pas cette étiquette).

**What to build:**
1. **A1** : une séquence se ferme après une durée continue sous le plancher (proposée entre 0,5 et 1 s, recommandation du 28c), et tout de suite si la possession change d'équipe ou si le ballon meurt. Aujourd'hui ces deux cas ramènent le danger à 0 et ferment la séquence au pas suivant (`occasion.py`, `situation_danger`) : avec le délai, ils sont détectés explicitement. `ChanceEvent.end` reste l'instant où le danger passe sous le plancher, pas l'instant de la fermeture (lu par `01c`).
2. **A2** : « récupération » est séparée en deux valeurs selon le dernier toucheur, adversaire ou coéquipier (noms à proposer), dans `ShotEvent.origin`, `ChanceEvent.origin` et `ReceptionEvent.origin`. Les lecteurs de l'origine (`scripts/v2_indicators.py` vers les lignes 1358 et 1453, `scripts/measure_v2.py` vers les lignes 912 à 916) comptent par nom d'origine : les deux nouvelles valeurs y apparaissent séparément, avec leur somme rapportée en face de l'ancienne « récupération ». Aucune comparaison littérale à « récupération » n'existe dans `scripts/` (vérifié le 26/11/2026). L'origine des buts du `v2-realisme/19e` (`scripts/v2_chain.py`, `goal_origin`) lit le journal, pas cette étiquette : non concernée.
3. Facultatifs A3 à A5 du 28c : non repris (aucun effet sur le découpage des moments), sauf si l'analyse montre le contraire.

**Attributs :** aucun.

**Constantes à proposer avant le code :** durée sous le plancher avant fermeture ; noms des deux origines.

**Blocked by:** — (`v2-collectif/28c` livré le 08/11/2026).

**Bloque :** 01b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : la fermeture se règle dans `ChanceTracker.update` sans changer le calcul du danger ; le dernier toucheur est déjà connu au moment du calcul de l'origine.
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs avant/après à graines fixées (environ 2 h 30).

## Tests

- **Scène :** danger qui passe sous le plancher pendant 0,3 s puis remonte : une seule séquence ; perte du ballon pendant la séquence : fermeture immédiate.
- **Non-régression du jeu :** à graine fixée, 3 matchs : empreintes des images, du ballon, des buts et du journal identiques avant et après ; seules `chances`, `shots[*].origin` et `receptions[*].origin` peuvent différer.
- **Mesure :** grosses occasions par match avant et après sur 50 matchs (graine d'audit), part des séquences fusionnées, répartition des deux nouvelles origines.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Exception respectée : aucun tirage ajouté, aucune lecture de `chances` ni de `origin` par le jeu (test de recherche ou test dédié) ; empreintes du jeu identiques avant et après sur 3 matchs à graine fixée
- [ ] Plus aucune paire de grosses occasions de la même équipe séparées de moins de la durée de fermeture sans changement de possession ni ballon mort (sur 50 matchs : 0)
- [ ] « Récupération » séparée en deux origines (tirs, occasions, réceptions) ; somme des deux rapportée en face de l'ancienne valeur dans les indicateurs, totaux inchangés
- [ ] Nombre de grosses occasions par match avant et après rapporté (le 7,7 du 28c baisse : écart expliqué)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
