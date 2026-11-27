# 22c: Coût de dessin de l'écran de match V2

**Ouvert le 27/11/2026** (décision du propriétaire, « B », à la clôture du `22b-cout-de-mise-en-page-du-terrain.md`).

**Constat (ticket 22b, banc `mesures/22-banc.sh`, ralenti × 6, deuxième conteneur)** : après le correctif de mise en page du 22b, la fluidité est à 76 % de `443e8c9` (36,7 contre 48,1 images/s). L'écart restant est diffus, réparti sur les tickets d'écran postérieurs à l'EM-04 (05 terrain, 06 bancs, 07 relief, 21a ballon, 21b filet, HUD, frises, statistiques), et se trouve au dessin et à la composition : par image, dessin 2,8 → 5,9 ms, tramage 0,9 → 3,9 ms, envoi au compositeur 0 → 2,2 ms ; tests de survol (pointeur sur le terrain) environ 30 % du temps, déjà présents avant l'EM-04.

**What to build:**
1. **Mesure poste par poste**, une variante jetable par élément, retiré ou simplifié, à partir de l'état courant : masque de relief des joueurs (sonde du 22b : envoi au compositeur 2,2 → 0 ms, sans gain d'images par seconde mesuré seul), vignette et dégradé de profondeur du gazon, motif du filet, ballon dessiné, bancs, frise de momentum, tests de survol (pointeur hors du terrain, à titre de comparaison). Compteurs Chrome et trace de chaque variante.
2. **Proposition chiffrée au propriétaire** : gain de chaque élément, et coût visuel de chaque simplification (captures).
3. **Correction** de ce que le propriétaire retient ; affichage inchangé pour ce qui n'est pas décidé autrement.

**Points de vigilance** : ceux du 22b (3 passages alternés ou plus, page animée contrôlée à chaque passage, même machine, empreinte de la trace, port libre) ; la machine dérive d'une série à l'autre (même état : 47,8 puis 39,8 images/s à une heure d'écart) : ne comparer qu'à l'intérieur d'une série.

**Blocked by:** aucun.

**Bloque :** aucun.

**Estimation** (27/11/2026) : analyse (variantes, traces) 60 min, proposition 20 min, développement 30 min, tests et mesures 45 min, intégration 30 min ; total 3 h 05 ; confiance faible. Au-delà du seuil de 2 h : à découper avant le code en « mesure et proposition » (1 h 20) et « correction » (selon les décisions). Temps machine à part : environ 8 variantes × 3 passages × 1 min 40, plus suite complète.

**Status:** à faire

## Acceptance criteria

- [ ] Gain de chaque élément mesuré (3 passages alternés, compteurs archivés) et proposition chiffrée remise au propriétaire
- [ ] Fluidité finale ≥ 90 % de celle de `443e8c9` sur le même banc et la même machine (critère du 22b), ou écart accepté par le propriétaire sur proposition chiffrée
- [ ] Affichage inchangé, ou changements décidés par le propriétaire (captures avant / après)
- [ ] `npm run build` OK, `npm run lint` sans nouvelle erreur, `npm test` vert ; suite complète au compte attendu ; V1 inchangée

## Comments
