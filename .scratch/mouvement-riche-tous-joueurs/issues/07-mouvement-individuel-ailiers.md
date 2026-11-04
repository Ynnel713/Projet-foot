# 07: Mouvement individuel pour les ailiers (AG/AD)

**What to build:** les ailiers n'ont AUCUN mécanisme de mouvement aujourd'hui quand ils ne sont pas un rôle actif du gabarit — même manque que le MOC. Leur donner un vrai mouvement cohérent avec leur poste : largeur du jeu (rester près de la touche), rentrée en diagonale vers l'axe selon la phase, moins de repli défensif qu'un latéral.

**Blocked by:** `plafond-vitesse-partage/01`.

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Un ailier décor montre un mouvement individuel cohérent (largeur + diagonale), mesurablement différent de la dérive générique actuelle
- [ ] Joueur sans attribut individuel disponible : repli neutre, comportement actuel
- [ ] Le mécanisme consomme le facteur partagé de `plafond-vitesse-partage/01`
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement inchangé
- [ ] Propriétaire valide le profil de mouvement de l'ailier AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `sequence_generator.py`/`motion.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder.
