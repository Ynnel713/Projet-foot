# 15c3: Tête au but

**Chantier :** `v2-realisme` (découpe du `15c`, validée par le propriétaire le 24/11/2026). **Priorité :** P2. **Catégorie :** exécution.

**Constat vérifié :** un ballon joué de la tête est un contrôle (`possession.attempt_control`) posé au pied, puis une décision au sol ; Heading n'est lu nulle part (24/11/2026).

**What to build:** le tir de la tête passe par la résolution physique du tir (`05a`) avec la physique du `15c2` : frappe plus lente qu'au pied, visée vers le bas, gardien ; têtes cadrées et buts de la tête mesurés (profils Heading 99 contre 11).

**Attributs :** contexte « tête au but » (Heading, Finishing ; poids à proposer) ; Composure reste dans le tir existant (pas de double comptage).

**Blocked by:** `15c2`. **Bloque :** `15f`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

**Total (travail effectif) : 2 h**, détail posé au lancement. Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Effet mesuré en scène et en série de 50 matchs, indicateurs globaux dans le bruit
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; durée réelle relevée

## Comments
