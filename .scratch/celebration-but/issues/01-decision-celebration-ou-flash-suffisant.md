# 01: Décision — une vraie célébration, ou le flash du tableau de score suffit ?

**What to build :** ce n'est PAS un ticket de construction — c'est une décision à prendre avec le propriétaire avant d'écrire la moindre ligne de code. Constat (23/10/2026) : aucune animation de célébration n'existe aujourd'hui (vérifié, zéro trace dans le code) — un but se termine net sur le geste technique. Mais le choix esthétique déjà posé dans `docs/PRD_PRODUIT.md` (« Football Manager 2D », crédibilité perçue plutôt que précision métrique) pourrait vouloir dire que le flash du tableau de score EST la célébration voulue par le projet, pas un manque à combler.

**Blocked by:** None.

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Propriétaire tranche explicitement : flash du tableau de score suffisant (fermer ce ticket sans suite), OU une vraie séquence de célébration des joueurs est voulue (dans ce cas, créer un ticket de construction dédié avec amplitude/durée à valider, en cohérence avec l'esthétique FM2D déjà choisie — pas une célébration trop réaliste/détaillée qui romprait le style minimaliste)
- [ ] Si construction retenue : vérifier la cohérence avec `but-contre-son-camp/02` (pas de célébration pour un but contre son camp)

**Note :** Aucun fichier sous exception touché par ce ticket lui-même (c'est une décision, pas du code) — le futur ticket de construction, s'il est créé, touchera `templates.py`.
