# 10b2: Le défenseur central ne prend la couverture que si sa place reste tenue

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (après le 10b, première source de sorties non couvertes des centraux). **Catégorie :** décision.

**Origine :** mesure du ticket 10b (18/11/2026, 50 matchs appariés) ; décision du propriétaire du 18/11/2026 : « Ticket séparé ».

**Constat vérifié :** le rôle de couverture (`defense.py`, point à `COVER_DEPTH_M` = 6 m derrière le porteur, porteur dans la moitié défendue) revient au premier arrivé sur ce point, quel que soit son poste. Le 10b ne l'a pas restreint (périmètre validé : presser, marquer). Après le 10b, un central couvre à plus de 10 m de sa place sans partenaire à 5 m ou moins de celle-ci pendant 3,28 min par match (contre 1,08 pour le marquage et 0,84 pour le pressing ; 3,62 avant le 10b) ; place menacée (adversaire à 20 m ou moins) 3,21 min. Sortie : `.scratch/v2-realisme/mesures/10b-comparaison.txt`, trace `MatchTrace.line_exits` (rôle `couverture`).

**What to build:** Appliquer au rôle de couverture la règle du 10b (`DefensiveRoles._leaves_uncovered`) : un central dont le point de couverture est une sortie (`line_exit`) ne le prend que couvert ; sinon la couverture revient au premier arrivé parmi les autres. À décider avec le propriétaire : si personne d'autre n'est libre, le central couvre-t-il quand même (comme le presseur) ou personne ne couvre (comme le marquage) ?

À traiter aussi (réserve A2 de l'expert au 10b, 18/11/2026) : un couvreur compté pour autoriser la sortie d'un central (`_leaves_uncovered`, lu dans `free`) peut recevoir ensuite un autre rôle dans le même tick (marquage d'un attaquant suivant, suivi d'un receveur) et ne plus être libre pour la compensation ; le réserver une fois retenu.

**Attributs :** aucun

**Lien avec l'existant :** prolonge le 10b (livré avec lui), sans nouvelle constante ; distinct du 10c (placement du défenseur le plus éloigné, sous la ligne, quand une passe en profondeur est possible), qui ne change pas l'attribution du rôle de couverture.

**Blocked by:** 10b (Le défenseur central ne quitte sa ligne que couvert).

**Bloque :** 10j.

**Status:** à faire (règle à confirmer par le propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 20 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 10** |

Confiance : moyenne. Hypothèses : la vérification du 10b se réutilise telle quelle ; la mesure du 10b (`10b-central-couvert.py`) sert de banc.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs avant/après (environ 1 h 20).

## Tests

- **Unitaires (scène contrôlée) :** porteur dans la moitié défendue, à 20 m devant la place du central, seul le central arrive le premier sur le point de couverture, place non couverte et menacée : un autre couvre ; milieu défensif sur sa place : le central couvre
- **Statistiques (séries de matchs) :** 50 matchs : minutes de couverture non couverte des centraux

## Acceptance criteria

- [ ] Règle (repli si personne d'autre n'est libre) et critères chiffrés validés par le propriétaire avant le code
- [ ] Couvertures non couvertes des centraux en baisse mesurée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
