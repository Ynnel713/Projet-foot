# 15c4: Remise et passe de la tête

**Chantier :** `v2-realisme` (découpe du `15c`, validée par le propriétaire le 24/11/2026). **Priorité :** P2. **Catégorie :** exécution.

**Constat vérifié :** un ballon joué de la tête est un contrôle (`possession.attempt_control`) posé au pied, puis une décision au sol ; Heading n'est lu nulle part (24/11/2026).

**What to build:** passe de la tête vers un coéquipier : dosage et direction avec la physique du `15c2` (remise en retrait, déviation dans la course, prolongation) ; réussite mesurée.

**Attributs :** contexte « remise de la tête » (Heading, Passing ; poids à proposer).

**Blocked by:** `15c2`. **Bloque :** `15f`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

**Total (travail effectif) : 1 h 45**, détail posé au lancement. Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Effet mesuré en scène et en série de 50 matchs, indicateurs globaux dans le bruit
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; durée réelle relevée

## Comments
