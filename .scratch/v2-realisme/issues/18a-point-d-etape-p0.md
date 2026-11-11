# 18a: Point d'étape après les fondations P0

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (vérifier la cohérence des mécanismes avant tout réglage). **Catégorie :** validation.

**Constat vérifié :** les repères de l'audit sont loin (37,6 tirs par équipe, conversion 5,7 %, 54,7 % des buts dans la surface, mesure 28b) ; plusieurs causes possibles se recouvrent.

**What to build:** Série exploratoire de 50 matchs une fois les P0 livrés : rapport complet (structure, gardien, conduite, tirs, xG, physique), écarts aux repères du 01c attribués à un mécanisme ou à la calibration ; liste des tickets P1 à avancer ou à créer. Aucun réglage.

**Attributs :** aucun

**Blocked by:** 02h (Validation de la structure : côtés, rôles, appels, distances); 03g (Validation du placement et des sorties du gardien); 04c (Validation : risque annoncé, probabilité calculée, résultat observé); 05g (Validation des tirs : trajectoire, cadrage, contres, arrêts); 06b (Indicateurs : occasion, exécution, gardien, par attribut); 17a (Carte des attributs : état réel de branchement); 19a (Performance momentanée : façade des notes); 19b (Journal des événements et chaîne de causes); 19c (Garde probabiliste); 19d (Banc : rendement selon la minute) (ajouté le 10/11/2026, audit de la roadmap); 19e (Origine des buts) ; 19f (Banc : tranches au temps joué et contrôles par tentative) (ajouté le 11/11/2026, réserves de l'expert sur le 19d).

**Bloque :** 18d.

**Status:** livré (11/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : rapport écrit, aucun code.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport complet

## Acceptance criteria

- [x] Rapport publié dans `docs/INDICATEURS_V2.md`
- [x] Chaque écart attribué (mécanisme ou calibration)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit de la roadmap (10/11/2026)

Source : `docs/AUDIT_ROADMAP_V2.md`. Ajouts au point d'étape, sans réglage : (1) section « condition physique » : ce que la fatigue change et ne change pas aujourd'hui (19d) ; (2) section « garde probabiliste » : résolutions hors garde (19c) et leur ticket ; (3) section « causalité » : part des buts par origine de chaîne (19b) ; (4) confirmation de l'ordre recommandé ensuite : 12d → 12e → 18d → 18e.

- [x] Rapport complété des trois sections ci-dessus

## Réalisation (11/11/2026)

- **Rapport** : `docs/INDICATEURS_V2.md` section 25 (25.1 repères R1 à R7, 25.2 autres indicateurs, 25.3 condition physique, 25.4 garde probabiliste, 25.5 causalité, 25.6 tickets et ordre). Chaque écart est attribué à un mécanisme ou à la calibration, avec son ticket.
- **Série** : la série de 50 matchs du 19f (`.scratch/v2-realisme/mesures/19f-det1.*`), jouée sur le moteur actuel (`681d9e0`, inchangé depuis : le 19f ne touche que le banc), sert de série exploratoire ; aucune série nouvelle. Déterminisme : `19f-det2.*` (10 premiers matchs rejoués, valeurs identiques). Origine des buts : `19f-chaine.json` (20 matchs).
- **Constats principaux** : tir et gardien dans l'ordre de grandeur (conversion 9,9 %, buts dans la surface 61 %) ; course loin pour une cause de mécanisme unique (intensité 1,0 par défaut : 14,0 km, 36,9 % de la distance au-dessus de 19,8 km/h) ; volume de tirs (24,3 par équipe) et passes (844 par match) liés au choix du porteur (conduite 73 %) ; coups de pied arrêtés : 0,9 % des buts (réel environ 23,5 %).
- **Ordre confirmé** : 12d → 12e → 18d → 18e. Compléments écrits dans 18d, 18e et 16g. Aucun ticket créé (relance par les DC à relire après le 18d).
- **Suite** : aucun code modifié ; suite complète de l'état actuel (19f, `bdffb8d`) : 2 745 passés, 14 désélectionnés, égal à l'attendu de `CLAUDE.md` tel que mis à jour au 19f (2 741 + 4 tests du 19f).
- **Durée** : estimée 1 h 30, réelle environ 1 h (− 33 %) : aucune série nouvelle à lancer ni à dépouiller (celle du 19f sert), aucun test à écrire (rapport seul ; le poste « tests » de l'estimation était sans objet).

## Comments

- 11/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ, réserves acceptées par le propriétaire (« Considère que je valide automatiquement toutes les recommandations, tous les conseils d'expert et tous les commits si la situation est favorable », 11/11/2026).
  - A1 : « ticket 14 » mal désigné pour les passes longues et en profondeur → `v2-collectif/32a` (et 32b), 14a pour la portée physique ; corrigé dans la section 25 au commit suivant (documentation).
  - A2 : R1 et R7 classés « mixte » (calibration du choix du porteur au 18d ; mécanisme des passes en profondeur et longues) ; corrigé au commit suivant.
  - A3 : `CLAUDE.md` attend déjà 2 745 depuis le commit du 19f (`bdffb8d`) ; phrase du ticket précisée.
  - A4 : compléments écrits dans 18d, 18e et 16g commités avec le 12d, sous sa revue.
  - A5 (facultatif) : fautes rattachées au 18d ou au 18e, possession d'équipe hors fourchette, lien Opta, repère DC non sourcé ; corrigé au commit suivant.
