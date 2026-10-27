# 10: Transition attaque-défense

**What to build:** À la perte du ballon, chaque joueur réagit selon sa position, son rôle, ses capacités et le contexte : les plus proches contre-pressent, d'autres protègent l'axe, d'autres sprintent vers leur zone. Pas un ordre universel de repli.

**Attributs :** Work Rate, Anticipation, Concentration, Teamwork ; Pace + Acceleration.

**Blocked by:** 03, 07, 09.

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] Temps de réaction moyen au repli dans une fourchette réelle (Bundesliga 2010/11 : ballon récupéré en environ 1 s par les meilleures équipes ; à préciser)
- [ ] Le choix entre contre-presser et se replier dépend mesurablement de la distance au ballon et du rôle
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée

**Reporté du ticket 05 (27/10/2026, décision du propriétaire) :** avec la ligne défensive à sa hauteur réelle, tirs et buts sortent des fourchettes (20 matchs : 18,1 tirs par équipe, 4,7 buts par match ; réel 8-15 et 2-3,5). Les tirs de contre-attaque après une récupération dans son camp doublent (4,8 → 9,5 par match) : les blocs se croisent plus haut et plus serrés, et personne ne se replace encore à la perte. Critère ajouté : ramener tirs de contre, tirs et buts vers les fourchettes réelles par le comportement de repli, sans baisser la ligne du ticket 05.
