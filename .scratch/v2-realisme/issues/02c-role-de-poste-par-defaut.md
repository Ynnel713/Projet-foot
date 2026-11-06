# 02c: Rôle de poste par défaut, porté par le joueur et tracé

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les placements et appels différenciés s'appuient sur un rôle). **Catégorie :** données.

**Constat vérifié :** aucun rôle de poste dans `v2engine/` : `PlayerState` porte seulement `poste` ; le bloc est une mise à l'échelle uniforme de la forme de départ (`bloc.py:178-199`).

**What to build:** Une table de rôles (par exemple latéral défensif ou offensif, milieu récupérateur, relayeur, meneur, ailier de couloir ou intérieur, avant-centre de profondeur ou pivot) et un rôle par défaut pour chaque poste ; le rôle est porté par l'état du joueur et écrit dans la trace. Aucun effet sur le jeu dans ce ticket (les effets arrivent en 02d, 02e et 09).

**Hors de ce ticket :** choix du rôle par le coach (13i) ; effets des rôles sur les placements, les appels et les déplacements (02d, 02e, 09).

**Décision du propriétaire (06/11/2026) :** les catégories de la colonne « Catégorie » de la base (mezzala, box to box, regista, pivot, buteur axial, piston, ailier inverse, meneur...) donnent chacune un rôle dédié ; un joueur sans catégorie reçoit le rôle standard de son poste. Le rôle dépend donc du poste **et** de la catégorie (`v2engine/roles.py`, table `poste × catégorie`, 20 rôles documentés avec leur intention). Une catégorie non prévue pour le poste (un DC dit « lateral defensif ») donne le rôle par défaut.

**Attributs :** aucun

**Blocked by:** 02a (Côté gauche ou droit selon le poste, et non selon le nom).

**Bloque :** 02d, 02e, 09c, 13h.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 60 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : élevée. Hypothèses : table de données, aucune décision ; estimation relevée de 1 h 40 à 2 h 10 pour la prise en compte des catégories de la base (normalisation, table poste × catégorie, test sur toute la base).
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** chaque poste de la base a un rôle par défaut ; chaque catégorie prévue donne son rôle (casse, accents et espaces de fin ignorés) ; catégorie non prévue pour le poste : rôle par défaut ; trace : le rôle figure dans les instantanés
- **Intégration (toute la base) :** chaque joueur reçoit un rôle documenté
- **Intégration :** trace identique à la version précédente hors nouveau champ (empreintes des positions et du ballon comparées à HEAD à graine fixée)

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Table des rôles documentée (rôle, intention footballistique)
- [x] Rôle tracé ; aucun effet sur le jeu (mesures identiques à graine fixée)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 06/11/2026 : passage 1 de l'expert `APPROVED_WITH_RESERVATIONS` (A1 : « _ » non traité dans la normalisation, test de la base ne prouvant pas la reconnaissance des catégories réelles ; A2 facultatif : résumé pytest absent). A1 corrigée (underscores, test de la base exigeant que toute combinaison réelle non prévue figure dans une liste assumée de 5), puis passage 2 `APPROVED_WITH_RESERVATIONS` (seule réserve : confirmer la suite complète, obtenue : 2 440 passés, 14 désélectionnés, 13 min 32 s). QC `VALIDÉ`, clôture `VALIDÉ` (journal). Réserves acceptées d'office, règle permanente du propriétaire. Décision du propriétaire (06/11/2026) : chaque catégorie de la base (mezzala, box to box, pivot, buteur axial...) a un rôle dédié ; sans catégorie, rôle standard du poste. Constantes (noms de rôles et table) proposées par Claude, validées par délégation. Positions et ballon identiques à HEAD à graine fixée (empreintes `690a6a79ab83f125`, `c568db324140f3d1`). 5 combinaisons de la base sans rôle dédié (DC lateral defensif, DC second attaquant, BU ailier inverse, RB box to box, MOC ailier inverse) : rôle du poste. À reprendre en 02d, 02e et 09 : les comportements propres à chaque rôle. Le chiffre « Attendu » de `CLAUDE.md` passe à 2 440.
- Durée : estimée 2 h 10, réelle environ 1 h 55 (non chronométrée), écart environ − 12 % : table de données, deux passes de l'expert. Temps machine, hors total : suite complète 13 min 32 s (deux fois).
