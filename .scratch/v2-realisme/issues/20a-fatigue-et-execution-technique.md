# 20a: La fatigue dégrade l'exécution technique

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (un excellent tireur de loin garde sa note, mais sa frappe de la 85e est moins sûre). **Catégorie :** exécution.

**Constat vérifié :** passes, contrôles, frappes et tacles lisent la note brute quel que soit l'état du joueur ; la fatigue ne touche que la vitesse maximale (`movement.py:60`).

**What to build:** Par la façade (19a), la réserve d'énergie (12e) baisse la note **exprimée** des gestes techniques, d'autant plus que le geste demande de la puissance ou de l'équilibre (frappe de loin, centre long, passe longue, tacle) et peu pour un geste simple (passe courte, contrôle facile). L'effet élargit la dispersion de l'exécution (écart d'angle du 35b, erreur de dosage) au lieu de plafonner la réussite : la frappe exceptionnelle reste possible, la frappe ratée devient plus fréquente. Stamina n'agit pas ici (elle règle la réserve, 12e).

**Attributs :** aucun nouveau ; note exprimée de Passing, First Touch, Crossing, Finishing, Long Shots, Technique, Tackling.

**Blocked by:** 19a, 12e.

**Bloque :** 20d ; `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : pente proportionnelle à la réserve manquante ; source réelle sur la baisse de précision en fin de match à chercher.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** même tireur, réserve pleine puis basse, 2 000 frappes de 25 m : cadrage en baisse, frappes au-dessus du 95e centile d'xG après frappe encore présentes
- **Unitaires (scène contrôlée) :** passe de 8 m sans pression : réussite quasi inchangée
- **Statistiques (séries de matchs) :** 50 matchs : réussite des passes longues et cadrage par tranche de 15 minutes (19d)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Baisse mesurée sur les gestes exigeants, faible sur les gestes simples
- [ ] Queue exceptionnelle présente pour le joueur fatigué ; hiérarchie des notes conservée à fatigue égale
- [ ] Toute note lue passe par la façade de la condition (`v2-realisme/19a`), jamais par `player_attribute` directement
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
