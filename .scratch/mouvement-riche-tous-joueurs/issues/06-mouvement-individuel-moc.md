# 06: Mouvement individuel pour le MOC

**What to build:** le MOC n'a AUCUN mécanisme de mouvement aujourd'hui (ni dédoublement, ni couverture, ni initiative) — exactement le même manque que les DC/gardien avant leurs tickets. Lui donner un vrai mouvement cohérent avec son rôle : déplacements entre les lignes, recherche d'espace dans le dos du milieu adverse, plutôt qu'une position figée ou une dérive générique.

**Blocked by:** `plafond-vitesse-partage/01`.

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Le MOC montre un mouvement individuel cohérent avec un rôle de meneur de jeu (déplacement entre les lignes), mesurablement différent de la dérive générique actuelle
- [ ] Joueur sans attribut individuel disponible : repli neutre, comportement actuel
- [ ] Le mécanisme consomme le facteur partagé de `plafond-vitesse-partage/01`
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement inchangé
- [ ] Propriétaire valide le profil de mouvement du MOC AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `sequence_generator.py`/`motion.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder.
