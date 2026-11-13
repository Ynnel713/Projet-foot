# 31a: Jeu à une touche (remise, passe de première)

**Découpé du ticket 31 le 13/11/2026** (validé par le propriétaire : « Oui vas y »). Détail : `31-premiere-touche.md`, point 1.

**What to build:** Sur une passe qui arrive, le receveur peut jouer sans contrôler (remise, passe à une touche) quand une passe suivante est prête, que la pression est supportable et que sa technique le permet. Decisions choisit entre jouer de première et contrôler ; le plan de passe du ticket 14 donne la suite préparée. Aujourd'hui, toute réception passe par un contrôle puis 1,7 à 2,9 s d'attente (`possession.reception_delay_s`).

**Hors de ce ticket :** contrôle orienté (31b), durée de réception (31c), tir de première (`34a`), difficulté de la passe selon l'arrivée du ballon (`36a` : ballon fort, de côté, de dos).

**Attributs :** First Touch et Technique (réussite du geste), Anticipation (préparer le geste), Decisions (choisir). Rayons fixés dans `docs/CARTE_ATTRIBUTS_V2.md` avant le code, sans double comptage (`v2-collectif/18`).

**Blocked by:** 14 (livré) ; `v2-realisme/07a`, `07c`, `07e`, `08c` (livrés) : démarrable.

**Bloque :** 31b, `34a`, `36a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 60 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **2 h 45** |

Confiance : moyenne. Hypothèses : la décision existante (`decision.decide`) évalue les options au moment de la réception ; l'exécution réutilise la passe existante avec une pénalité de geste ; pas de nouvelle géométrie d'arrivée (36a).
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs avant/après (environ 25 min).

## Acceptance criteria

- [ ] Constantes et chiffres réels (part des passes jouées à une touche : sourcée ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène contrôlée : passe suivante prête et pression faible, un joueur à First Touch et Technique élevés joue de première plus souvent qu'un joueur à notes basses, jamais à 100 % ni 0 %
- [ ] Scène contrôlée : la pression adverse réduit les jeux de première
- [ ] En match (50 matchs, graines du banc) : part de passes à une touche, durée de possession individuelle, une-deux et troisième homme (ticket 14), passes par match et réussite, comparés avant et après
- [ ] Rayon des attributs conforme à la carte, sans double comptage ; test de rayon à jour
- [ ] Indicateur ajouté au banc et défini dans `docs/INDICATEURS_V2.md`
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
