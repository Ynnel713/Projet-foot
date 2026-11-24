# 15a3: Sélection transitive des joueurs désignés sur un ballon aérien

**Chantier :** `v2-realisme` (réserve A1 de l'expert au ticket `15a2`, 24/11/2026, acceptée par le propriétaire : « Accepter, corriger en ticket »). **Priorité :** P3. **Catégorie :** décision.

**Constat vérifié (15a2) :** `jeu_aerien._compare` (règle double du maintien) n'est pas un ordre total dès que trois coéquipiers de seniorités différentes sont en concurrence. Exemple de l'expert : S premier désigné (contact 1,0 s, arrivée 1,0 s), J1 nouveau (0,9 s, 0,8 s), J2 nouveau (1,0 s, 0,5 s) : J1 avant J2, S avant J1, J2 avant S. Le tri rend alors un ordre qui dépend de l'ordre de la liste des joueurs (déterministe, mais pouvant contredire la règle).

**What to build:** sélection en deux temps (correctif proposé par l'expert) : classer les non-désignés par la clé neutre (contact arrondi, arrivée, nom) ; pour chaque place, premier puis second, le titulaire du pas précédent la garde sauf si le meilleur prétendant qui le déplace selon la règle double le déplace. Mêmes résultats sur les cas à deux joueurs.

**Attributs :** aucun. **Constantes :** aucune.

**Blocked by:** `15a2` (livré). **À faire avant ou avec :** `15b`.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 05** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs appariée (environ 48 min), suite complète (environ 22 min).

## Tests

- Scène S, J1, J2 ci-dessus : même résultat pour les 6 permutations de la liste des joueurs, conforme à la règle double.
- Scènes du `15a` et du `15a2` inchangées.
- Série : changements rapides du premier non dégradés (7,4 % au `15a2`) ; premier contrôle du corps après un centre surveillé (+ 4 points au `15a2`).

## Acceptance criteria

- [ ] Scène à trois joueurs indépendante de l'ordre des joueurs
- [ ] Scènes à deux joueurs inchangées
- [ ] 50 matchs appariés sans dégradation ; déterminisme à graine fixée ; suite complète au compte attendu
