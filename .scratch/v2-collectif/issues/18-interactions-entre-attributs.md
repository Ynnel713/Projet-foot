# 18: Interactions entre attributs, sans double comptage

**What to build:** Faire jouer les paires du guide sur le comportement, pas seulement sur la réussite : Anticipation + Positioning, Vision + Decisions + Passing, Off the Ball + Acceleration + Pace, Work Rate + Stamina, Teamwork + Positioning, Dribbling + Flair + Decisions, Concentration + Anticipation, Crossing + Vision + Decisions, Composure + Finishing, Pace + Acceleration + Positioning. **Règle anti double comptage** : un effet donné n'est compté qu'une fois (si Anticipation améliore déjà le départ, pas de second bonus identique ailleurs). Distinguer effets directs et indirects : Leadership améliore la coordination, pas la précision de ses propres passes.

**Attributs :** Tous ; audit de `docs/CARTE_ATTRIBUTS_V2.md`.

**Blocked by:** 02 (puis appliqué à chaque ticket).

**Status:** livré en partie (26/10/2026) : règle, table, audit, garde automatique et correction A1 ; les deux critères de mesure en match sont reportés (voir plus bas)

**Point de vigilance :** ce ticket fixe une règle, puis sert de grille de relecture pour chacun des autres.

- [x] Table des interactions écrite dans la carte des attributs, chaque effet avec un seul attribut responsable
- [ ] Test de cohérence : améliorer un attribut produit l'effet attendu dans ses situations, sans rendre le joueur meilleur partout — reporté : vérifié attribut par attribut dans chaque ticket qui le branche (grille de relecture, question 5, `--profil`) ; la garde automatique couvre la partie statique
- [ ] Écarts entre joueurs extrêmes dans des fourchettes réelles (pas d'écart excessif) — reporté au ticket 22 (calibration), mesuré avec `--profil`
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée

## Réalisé (26/10/2026)

- Règle (R1 à R5, plafond d'écart), table des interactions, audit du moteur et grille de relecture : section « Interactions et règle anti double comptage » de `docs/CARTE_ATTRIBUTS_V2.md`.
- Correction A1 : la réussite du tacle ne dépend plus que de Tackling.
- Dérogations : A2 (Composure dans le tir, jusqu'au ticket du tir) et A3 (Strength et Balance du porteur, jusqu'à l'étape duels), validées ; A8 (note du gardien, jusqu'à la phase 9) confirmée le 26/10/2026. A9 (pression du receveur comptée deux fois dans la valeur d'une passe) reportée au ticket 13.
- Mesure sur 20 matchs avant et après A1 : tacles 38,4 → 39,45 ; buts 3,65 → 3,45 ; tirs par équipe 11,35 → 11,05 ; autres indicateurs à moins de 1 %.
- Garde automatique : `tests/test_v2engine_rayon_attributs.py`.
