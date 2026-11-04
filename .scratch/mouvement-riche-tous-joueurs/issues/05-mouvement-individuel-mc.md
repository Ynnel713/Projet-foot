# 05: Mouvement individuel distinct pour le MC

**What to build:** symétrique du ticket 04 (MDC) — le MC doit avoir son propre profil de mouvement, distinct du MDC : rôle box-to-box, amplitude plus large et plus impliquée dans les deux transitions (offensive et défensive) qu'un MDC.

**Blocked by:** `plafond-vitesse-partage/01`.

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Sur un même clip/contexte, un MC montre une amplitude de mouvement mesurablement plus large qu'un MDC (voir ticket 04)
- [ ] Joueur sans attribut individuel disponible : repli neutre, comportement actuel
- [ ] Le mécanisme consomme le facteur partagé de `plafond-vitesse-partage/01`
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement inchangé
- [ ] Propriétaire valide le profil de mouvement du MC AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `sequence_generator.py`/`motion.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder. À séquencer avec le ticket 04 (MDC) de ce dossier, puisque les deux touchent le même mécanisme aujourd'hui partagé.
