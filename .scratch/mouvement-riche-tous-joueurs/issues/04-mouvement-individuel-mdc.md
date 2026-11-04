# 04: Mouvement individuel distinct pour le MDC

**What to build:** aujourd'hui, MDC et MC partagent EXACTEMENT le même mécanisme de mouvement (même règle, aucune distinction de poste) — alors que le MDC a un rôle tactique différent : discipline de position, écran devant la défense, amplitude de déplacement plus réduite et plus orientée couverture que le MC. Lui donner son propre profil de mouvement, distinct de celui du MC.

**Blocked by:** `plafond-vitesse-partage/01`.

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Sur un même clip/contexte, un MDC et un MC montrent des trajectoires mesurablement différentes (amplitude, orientation), pas la même règle recopiée
- [ ] Le MDC reste proche de sa zone de couverture — amplitude plus faible qu'un MC, validé visuellement par le propriétaire
- [ ] Joueur sans attribut individuel disponible : repli neutre, comportement actuel
- [ ] Le mécanisme consomme le facteur partagé de `plafond-vitesse-partage/01`
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement inchangé
- [ ] Propriétaire valide le profil de mouvement du MDC AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `sequence_generator.py`/`motion.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder. À séquencer avec le ticket 05 (MC) de ce dossier, puisque les deux touchent le même mécanisme aujourd'hui partagé.
