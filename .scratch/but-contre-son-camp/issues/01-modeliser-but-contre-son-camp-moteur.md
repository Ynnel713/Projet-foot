# 01: Modéliser le but contre son camp dans le moteur de résultats

**What to build:** aujourd'hui un but est TOUJOURS attribué à un attaquant de l'équipe qui marque — aucun concept de « but contre son camp » n'existe dans `events.py`/`simulation.py`. Ce ticket introduit ce cas de figure au niveau du moteur statistique : un but peut être crédité comme marqué par un défenseur de l'équipe adverse (qui ENCAISSE), sans qu'aucun passeur ne soit crédité côté attaque, sans changer la fréquence globale de buts déjà calibrée, et sans jamais recalculer un résultat déjà décidé par ailleurs.

**Blocked by:** None, mais chantier le plus engageant de ce lot — étude technique (TRD) fortement recommandée avant tout code, vu que ça touche le modèle de données du moteur de résultats lui-même.

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Un but peut être généré comme contre son camp, crédité au joueur défenseur qui l'a provoqué, sans passeur
- [ ] La fréquence des buts contre leur camp reste rare et cohérente avec la fréquence réelle observée en football (constante à valider avec le propriétaire)
- [ ] Les statistiques déjà affichées ailleurs (buteurs, classement) restent cohérentes avec ce nouveau cas (le but compte pour l'équipe qui en bénéficie, pas de buteur dans le classement des buteurs du joueur fautif)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Aucune régression sur la distribution de buts déjà calibrée (critère de succès du PRD)
- [ ] Propriétaire valide la fréquence et le mécanisme de tirage AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `events.py`/`simulation.py` sont le moteur Poisson lui-même, le fichier le plus protégé du projet — exception explicite et étude technique (TRD) requises avant la moindre ligne de code.
