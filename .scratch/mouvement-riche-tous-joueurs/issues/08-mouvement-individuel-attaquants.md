# 08: Mouvement individuel offensif pour les attaquants (BU/SA/ATT)

**What to build:** les attaquants ont aujourd'hui un mécanisme de repli défensif, mais SEULEMENT côté `opponent` (leur équipe encaisse) — côté `scorer`, quand ils ne sont pas eux-mêmes le rôle actif du gabarit (ex. un remplaçant offensif, ou un attaquant non impliqué dans ce but précis), ils n'ont aucun mouvement individuel. Leur donner un vrai mouvement offensif (appel dans la profondeur, décrochage) côté `scorer` quand ils sont décor, symétrique au mécanisme défensif déjà validé côté `opponent`.

**Blocked by:** `plafond-vitesse-partage/01`.

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Côté `scorer`, un attaquant décor (non impliqué comme rôle actif) montre un mouvement individuel cohérent avec un appel offensif, mesurablement différent de la dérive générique actuelle
- [ ] Le mécanisme défensif déjà existant côté `opponent` n'est pas régressé
- [ ] Joueur sans attribut individuel disponible : repli neutre, comportement actuel
- [ ] Le mécanisme consomme le facteur partagé de `plafond-vitesse-partage/01`
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement inchangé
- [ ] Propriétaire valide l'amplitude/les règles de mouvement offensif de l'attaquant AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `sequence_generator.py`/`motion.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder.
