# 94: Tolérance « à hauteur » du hors-jeu portée à 0,5 m

**What to build:** La tolérance sous laquelle attaquant et avant-dernier défenseur sont jugés à hauteur passe de 0,3 m à 0,5 m (constante validée par le propriétaire le 29/10/2026), pour rapprocher le nombre de hors-jeu des chiffres réels.

**Status:** implémenté (29/10/2026) — en attente de /valider-ticket-simulafoot

- [x] OFFSIDE_TOLERANCE_M = 0,5 m (validé par le propriétaire)
- [ ] Hors-jeu par match dans la fourchette réelle 3,2-3,5, mesuré sur 20 matchs (`uv run python -m scripts.measure_v2 20`)
- [ ] Tirs par équipe toujours dans la fourchette réelle sur la même mesure
