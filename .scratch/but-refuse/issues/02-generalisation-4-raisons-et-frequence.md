# 02: Généralisation aux 4 raisons et calibrage de la fréquence

**What to build:** étend le mécanisme validé par le POC (ticket 01) aux 3 autres raisons fixes — main, faute en amont de l'action, VAR qui revient sur une décision (ex. penalty finalement refusé) — et à l'ensemble des gabarits (pas seulement le pilote). Calibre la fréquence d'apparition d'un but refusé sur l'échantillon de référence (rare, mais pas absent).

**Blocked by:** 01 (POC — un but refusé pour hors-jeu).

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Les 4 raisons (hors-jeu, main, faute en amont, VAR) sont chacune représentées sur l'échantillon de référence
- [ ] La raison affichée au bandeau est toujours cohérente avec le type de raison tiré (pas de « Hors-jeu » affiché pour une raison « main »)
- [ ] Fréquence mesurée sur l'échantillon conforme à la cible validée avec le propriétaire (rare, de l'ordre de quelques occasions rhabillées par échantillon, pas un but refusé à chaque match)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Aucune régression sur les clips hors but-refusé
- [ ] Propriétaire valide la fréquence exacte et la table de raisons AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `narrative.py`, `templates.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder.
