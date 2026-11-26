# 10m1: Repli en hauteur à la perte, et remontée de la ligne dès que le ballon est contenu

**Chantier :** `v2-realisme` (découpé de 10m le 26/11/2026, demande du propriétaire). **Priorité :** P1. **Catégorie :** placement.

**Constat vérifié :** voir 10m. À la perte, la place de référence du bloc monte avec le ballon. Le centre de l'équipe avance au lieu de reculer : −0,25 m/s à la dernière mesure du banc, où une valeur positive signifie « vers son but ». Piège connu (ticket `v2-collectif/10`, 03/11/2026) : interdire la montée fait reculer l'équipe, mais le hors-jeu tombe de 2,0 à 0,69 par match.

**What to build:**
1. **Cible de repli en hauteur.** À la perte, la place de référence du bloc vise une hauteur en retrait du ballon, d'une profondeur à proposer, au lieu de suivre le ballon vers l'avant.
2. **Ballon contenu.** Condition lue sur le monde perçu, définition à proposer : porteur adverse pressé (presseur à moins de `PRESSED_M`), porteur tourné vers son propre but, ou passe adverse en retrait.
3. **Remontée.** Dès que le ballon est contenu, la ligne remonte progressivement vers sa hauteur de défense placée, avec sa règle de hors-jeu inchangée. Le repli ne bloque jamais la ligne en bas.

La profondeur de repli est un paramètre d'équipe, lisible plus tard par le style (13c, 13j), le score (`v2-collectif/21`) et la fatigue (20e), sans seconde mécanique.

**Point de vigilance :** le contre-pressing du ticket 10 place très tôt un presseur à moins de 3 m du porteur. Si « porteur pressé » suffit à faire remonter la ligne, le repli peut s'annuler à presque chaque perte. La définition du « ballon contenu » doit en tenir compte, par exemple par une durée de pression ou une condition sur l'orientation du porteur ; les critères de recul et de hors-jeu détectent ce conflit.

**Attributs :** aucun nouveau. Work Rate garde l'intensité du repli (ticket 10) ; Teamwork garde l'écart toléré à sa place.

**Lien avec l'existant :** premier morceau de 10m. Le resserrement en largeur est au 10m2.

**Blocked by:** 01f (livré).

**Bloque :** 10m2, 10n, `v2-collectif/22b`.

**Dépendance non réciproque :** 01f (livré) n'est pas modifié ; sa ligne « Bloque » ne cite pas 10m1.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : la place de référence (`bloc.py`) accepte une cible de transition ; la notion de porteur pressé existe déjà (`PRESSED_M`).
Temps machine, non compté : suite complète (environ 10 min en session cloud) ; 50 matchs avant/après.

## Tests

- **Unitaires (scène contrôlée) :**
  - perte au milieu de terrain, porteur adverse libre : 3 s après, centre de l'équipe plus bas qu'à la perte ;
  - même perte, ballon contenu au sens de la définition validée : la ligne remonte dans le délai de remontée validé.
- **Statistiques (séries de matchs) :** 50 matchs avant/après, mêmes graines : vitesse de recul, latence, bloc reformé, hors-jeu par match, tirs de contre après récupération, part des buts issus d'une récupération.

## Acceptance criteria

- [ ] Profondeur de repli, définition du « ballon contenu » et vitesse de remontée proposées et validées par le propriétaire avant le code ; hors-jeu actuel relevé avant le code
- [ ] Vitesse de recul du centre de l'équipe (positive = vers son but) positive, ou nettement plus élevée qu'avant, et bloc reformé plus vite ; seuils chiffrés proposés avant la mesure
- [ ] **Hors-jeu au moins 1,5 par match** (seuil du propriétaire, 26/11/2026) : estimation ponctuelle sur 50 matchs au moins 1,5, intervalle de confiance rapporté ; si sa borne basse descend sous 1,2, série portée à 200 matchs
- [ ] Tirs de contre après récupération et part des buts issus d'un ballon gagné à l'adversaire (catégories « récupération » et « erreur adverse » du 19e, rapportées séparément) en baisse ou stables (sens mesuré)
- [ ] Profondeur de repli exposée comme paramètre d'équipe
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
