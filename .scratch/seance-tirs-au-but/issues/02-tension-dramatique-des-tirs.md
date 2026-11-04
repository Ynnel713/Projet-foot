# 02: Tension dramatique de la séance (rythme crédible)

**What to build:** aujourd'hui `_penalty_shootout_score` tire un score de séance réaliste (répartition pondérée vers 5-4, 4-3, etc.) mais le ticket 01 se contente de l'exécuter tir par tir. Ce ticket ajoute le rythme dramatique attendu d'une vraie séance : variété visuelle entre les tirs (pas tous identiques), tension qui monte sur les derniers tirs, mise en scène distincte du tir décisif.

**Blocked by:** 01 (POC — une séance de tirs au but animée).

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Sur l'échantillon de référence, les tirs d'une même séance ne sont pas visuellement identiques (variation déterministe, même principe que les autres gabarits)
- [ ] Le tir décisif est visuellement distinct des tirs précédents (mise en scène, pas juste la position dans la liste)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat de la séance strictement inchangé
- [ ] Propriétaire valide que la tension perçue est crédible sur un échantillon de séances

**Note :** `templates.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder.
