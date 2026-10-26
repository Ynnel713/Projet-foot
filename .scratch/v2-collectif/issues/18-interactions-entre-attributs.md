# 18: Interactions entre attributs, sans double comptage

**What to build:** Faire jouer les paires du guide sur le comportement, pas seulement sur la réussite : Anticipation + Positioning, Vision + Decisions + Passing, Off the Ball + Acceleration + Pace, Work Rate + Stamina, Teamwork + Positioning, Dribbling + Flair + Decisions, Concentration + Anticipation, Crossing + Vision + Decisions, Composure + Finishing, Pace + Acceleration + Positioning. **Règle anti double comptage** : un effet donné n'est compté qu'une fois (si Anticipation améliore déjà le départ, pas de second bonus identique ailleurs). Distinguer effets directs et indirects : Leadership améliore la coordination, pas la précision de ses propres passes.

**Attributs :** Tous ; audit de `docs/CARTE_ATTRIBUTS_V2.md`.

**Blocked by:** 02 (puis appliqué à chaque ticket).

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** ce ticket fixe une règle, puis sert de grille de relecture pour chacun des autres.

- [ ] Table des interactions écrite dans la carte des attributs, chaque effet avec un seul attribut responsable
- [ ] Test de cohérence : améliorer un attribut produit l'effet attendu dans ses situations, sans rendre le joueur meilleur partout
- [ ] Écarts entre joueurs extrêmes dans des fourchettes réelles (pas d'écart excessif)
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
