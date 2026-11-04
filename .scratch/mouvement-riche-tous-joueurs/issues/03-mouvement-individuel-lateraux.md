# 03: Mouvement individuel réel pour les latéraux (LB/RB)

**What to build:** les latéraux ont aujourd'hui un mécanisme de dédoublement offensif, mais SEULEMENT quand leur équipe marque (côté `scorer`) — côté `opponent` (leur équipe encaisse), ils n'ont aucun mouvement individuel, juste la dérive générique. Leur donner un vrai mouvement défensif cohérent (repli sur leur couloir, resserrement vers l'axe selon la menace) côté `opponent`, symétrique en esprit au mécanisme offensif déjà validé côté `scorer`.

**Blocked by:** `plafond-vitesse-partage/01`.

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Côté `opponent`, un latéral montre un mouvement individuel cohérent avec un repli défensif, mesurablement différent de la dérive générique actuelle
- [ ] Le mécanisme offensif déjà existant côté `scorer` n'est pas régressé (clips identiques à avant sur ce côté)
- [ ] Joueur sans attribut individuel disponible : repli neutre, comportement actuel
- [ ] Le mécanisme consomme le facteur partagé de `plafond-vitesse-partage/01`
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement inchangé
- [ ] Propriétaire valide l'amplitude/les règles de mouvement défensif du latéral AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `sequence_generator.py`/`motion.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder. Touche le même fichier que les autres tickets de poste de ce dossier — à séquencer plutôt qu'à paralléliser avec eux pour limiter le risque de conflit, sans dépendance technique stricte entre eux.
