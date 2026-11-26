# 14b4: Qui met de l'effet : spin par type de frappe et lecture adverse

**Découpé du ticket 14b le 26/11/2026** (audit Magnus : `docs/AUDIT_MAGNUS_V2.md`). **Chantier :** `v2-realisme`. **Priorité :** P2 (gros levier de réalisme : sans lui, le solveur 14b1 ne sert à rien en match). **Catégorie :** exécution.

**Constat vérifié (26/11/2026) :** aucune frappe ne porte de type d'effet ; les types de frappe eux-mêmes manquent pour la plupart (centres variés : `v2-attributs-restants/11` ; corner rentrant / sortant : 16d ; coup franc direct : 16e ; finitions enroulées : `v2-attributs-restants/10a`, après la calibration). Les gestes préférés « Curls Ball » sont rangés (05a, 05b) sans effet.

**What to build:**
1. **Table d'effet par type de frappe existant** (constante produit) : axe (latéral, avant, arrière) et quantité de ω, avec le pied qui frappe donnant le sens (pied fort par défaut tant que `v2-attributs-restants/04a` n'est pas livré : sens tiré à pile ou face, noté comme provisoire). Types couverts ici : passe au sol courte (0), passe longue et changement de jeu, passe aérienne depuis le couloir (centre), corner vers la surface, coup franc frappé, tir hors de la surface. Point d'entrée unique, que 11, 16d, 16e et 10a affineront (type de centre, rentrant ou sortant, enroulé ou puissant). Quantités prises dans les repères figés au 14b1 (sourcing fait là-bas, pas ici).
2. **Visée inverse des passes avec effet** : `possession.pass_aim` / `pass_velocity` (direction de départ = cible − passeur aujourd'hui) utilisent la fonction de visée inverse du 14b3 (même tolérance, même repli : sans effet, visée droite) ; ajouté le 26/11/2026 (vérification du séquencement 14b2 / 14b3 : ni 14b2 ni 14b3 ne le couvraient).
3. **Pas de nouvelle loi de réussite** : la précision reste celle des lois existantes (Passing, Crossing, Long Shots, Finishing ; erreur du 23a / 23b quand ils seront livrés). L'effet change la forme du chemin, pas la probabilité de réussir (règle R1 : un effet, un calcul) ; aucun attribut lu dans ce ticket.
4. **Lecture adverse** : par défaut, défenseurs et gardien lisent la trajectoire réelle (comme aujourd'hui, `meeting_point`). Option à proposer au propriétaire : lecture de la courbe selon Anticipation (contexte du registre, ADR 0002), qui permettrait au gardien d'être trompé par l'effet ; à acter avant le code, sinon reportée à `v2-realisme/03l`.
5. **Mesure** : 50 matchs avant / après (passes, interceptions, centres réussis, tirs cadrés, buts, buts sur coup franc et corner).

**Attributs :** aucun (les attributs de geste arrivent avec 11, 16d, 16e, 10a, 05a, 05b).

**Cohérence attribut / comportement :** le geste préféré « Curls Ball » (rangé dans la famille des tirs, `tests/test_v2engine_rayon_attributs.py:514`, sans effet aujourd'hui) doit, une fois 14b4 livré, augmenter l'effet de ses frappes (tirs, centres, coups francs) ; branché par `v2-attributs-restants/05a` (centres, coups francs) et `05b` (tirs), qui lisent la table de ce ticket. Tant que ce n'est pas fait, l'écart est noté dans `docs/CARTE_ATTRIBUTS_V2.md` au moment de la livraison.

**Blocked by:** 14b2 (Passes sur trajectoire courbe) ; 14b3 (Tirs sur trajectoire courbe).

**Bloque :** 14c (rotation au rebond : il faut des ballons avec effet), 14d ; 16d ; 16e ; `v2-attributs-restants/11` ; `v2-attributs-restants/10a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 55 min |
| Tests unitaires et comportementaux | 40 min |
| Intégration et vérifications | 35 min |
| **Total (travail effectif)** | **2 h 35** |

Confiance : faible. Hypothèses : la table reste une constante par type (pas de choix tactique de l'effet ici) ; l'option « lecture selon Anticipation » est reportée (sinon + 1 h, ticket à part). Au-dessus du seuil de 2 h, examiné : la mesure de 50 matchs fait partie du ticket (premier changement de jeu de la série 14b), découpage non retenu.
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs avant / après.

## Tests

- **Unitaires (scène contrôlée) :** chaque type de frappe porte l'axe et la quantité de la table ; passe courte au sol : ω = 0 ; un centre depuis l'aile droite d'un droitier rentre vers le but
- **Statistiques (séries de matchs) :** 50 matchs : volumes et réussites des passes, centres, tirs dans le bruit ou écart expliqué ; écart latéral moyen des centres et coups francs relevé (repris par 14d)

## Acceptance criteria

- [ ] Table d'effet par type (axe, quantité, sens) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Décision sur la lecture adverse (réelle par défaut, ou selon Anticipation) actée avant le code
- [ ] Passes avec effet : arrivée à moins de 5 cm du point visé hors erreur d'exécution (scènes) ; replis ≤ 1 % des frappes avec effet sur 50 matchs (compteur de la trace)
- [ ] Aucun nouveau tirage de réussite ; aucun attribut lu (garde de rayon des attributs verte)
- [ ] Mesure 50 matchs publiée dans `docs/INDICATEURS_V2.md`
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
