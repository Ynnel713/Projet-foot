# 01: Styles du coach traduits en consignes d'équipe

**What to build:** Lire les styles du coach (`coaches.coach_styles`) dans le moteur V2 et les traduire en consignes d'équipe qui décalent des mécanismes déjà existants :

| Style | Mécanisme existant décalé | Effet attendu |
|---|---|---|
| Pressing | déclencheurs et hauteur du pressing (v2-collectif/08), contre-pressing après la perte (10), hauteur du bloc (05), intensité (12) | presse plus souvent et plus haut, contre-presse dès la perte ; s'use plus vite |
| Défensif | hauteur du bloc (05), soutien du porteur (06), appels (16) | bloc plus bas et plus compact ; moins de joueurs projetés |
| Offensif | appels complémentaires (16), surcharges (17), hauteur du bloc (05) | plus de joueurs au-delà du ballon ; plus exposé en transition |
| Contre attaque | transition offensive (11), valeur future de la passe (13) | après récupération, passe verticale et appels en profondeur privilégiés ; bloc plutôt médian |
| Possession | valeur de la passe (13), construction face au pressing (15), contre-pressing (10) | passes sûres préférées, tempo plus lent, moins de ballons longs ; récupère vite après la perte |

Les styles se cumulent (un coach peut en cocher jusqu'à 5) avec un plafond, comme en V1 (`_STYLE_MODIFIER_BOUNDS`).

**Attributs :** aucun nouveau. Les attributs restent responsables de la qualité d'exécution ; le style ne règle que l'intention collective.

**Blocked by:** v2-collectif/05, 08, 11, 13 (livrés) et 10, 12, 15, 16, 17 (pas encore livrés).

**Status:** découpé (05/11/2026, chantier `v2-realisme`, validé par le propriétaire ; D-V10 levée le 02/11/2026) en `v2-realisme/13a` (lecture des styles, consignes neutres), `13b` (Pressing), `13c` (Défensif), `13d` (Offensif), `13e` (Contre-attaque), `13f` (Possession et tempo), `13g` (largeur), `13h` (rôles selon la formation), `13i` (validation : critères de ce ticket repris). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

**Point de vigilance :** le style ne doit pas rendre une équipe meilleure ; il déplace le risque (le pressing gagne des ballons hauts mais laisse de l'espace dans le dos, le défensif encaisse moins mais tire moins). Sans coach ou sans style : comportement neutre.

- [ ] Définir dans `docs/INDICATEURS_V2.md` et ajouter à `scripts/v2_indicators.py` : récupérations dans le tiers adverse, joueurs dans la surface adverse, occasions concédées dans le dos, part de possession
- [ ] Chaque style produit un écart mesurable, dans le sens attendu, sur son indicateur (`scripts/v2_indicators.py`) : hauteur moyenne du bloc, récupérations dans le tiers adverse, passes par possession, part des passes vers l'avant après récupération, joueurs dans la surface adverse
- [ ] La contrepartie de chaque style est mesurable (ex. Pressing : plus de courses à haute intensité et plus d'occasions concédées dans le dos)
- [ ] Même équipe, mêmes joueurs, style différent : comportement différent ; différence de buts moyenne, sur au moins 200 matchs appariés par graine contre le même adversaire, avec son intervalle de confiance, non systématiquement en faveur d'un style
- [ ] Club sans coach ou sans style : indicateurs identiques à la version précédente
- [ ] Effet probabiliste, jamais binaire ; aucune double mécanique (v2-collectif/18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] `docs/TRD_V2.md` mis à jour : D-V10 levée, `coaches.py` ajouté à D-V02 (lecture seule) (02/11/2026)
- [ ] Suite V2 verte ; V1 inchangée
