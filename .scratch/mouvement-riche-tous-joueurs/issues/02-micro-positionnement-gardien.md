# 02: Micro-positionnement du gardien

**What to build:** aujourd'hui, le gardien est figé sur une position d'ancrage fixe (`_gk_base_position`) selon le contexte (scorer/adversaire, penalty...), sans variation individuelle. Donner au gardien un léger ajustement de placement cohérent avec le jeu (suivre l'angle de la menace, légers déplacements dans sa surface) — jamais une sortie de sa surface façon joueur de champ, jamais une influence sur l'issue déjà décidée (arrêt/but).

**Blocked by:** `plafond-vitesse-partage/01` (même raison que le ticket 01 de ce dossier). Indépendant du ticket 01 de ce dossier entre eux.

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Le gardien montre un micro-mouvement de placement cohérent avec la position du ballon/de la menace, pas une position figée à l'identique sur tous les clips
- [ ] Le gardien reste dans sa surface, jamais un déplacement de joueur de champ
- [ ] L'issue de l'action (but/arrêt déjà décidée par le moteur) reste strictement inchangée
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Aucune régression sur les gabarits à gardien actif existants
- [ ] Le mécanisme consomme le facteur partagé de `plafond-vitesse-partage/01`, ne recalcule pas son propre plafond/plancher
- [ ] Propriétaire valide l'amplitude du micro-mouvement AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `sequence_generator.py`/`motion.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder.
