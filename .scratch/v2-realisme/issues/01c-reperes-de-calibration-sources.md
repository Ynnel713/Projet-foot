# 01c: Repères de calibration : sources, définitions, compatibilité avec le banc

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les repères de l'audit ne deviennent bloquants qu'une fois leurs définitions vérifiées). **Catégorie :** documentation.

**Constat vérifié :** l'audit propose 8-15 tirs par équipe, 10-11 % de conversion, 80-90 % de buts dans la surface, 9-14 km, 5-20 appels, 2-5 % au-dessus de 19,8 km/h et 15-17 passes par minute ; `docs/INDICATEURS_V2.md` cite certaines sources, mais la définition d'un « appel » du banc (plus de 0,7 s au-dessus de 15 km/h) n'est pas forcément celle de la source (PLOS One 2022) et « temps » ou « distance » au-dessus de 19,8 km/h ne sont pas distingués.

**What to build:** Pour chacun des 7 repères : source primaire, population (ligue, saison), définition exacte, unité, indicateur du banc qui le mesure et écart de définition. Conclure pour chacun : critère bloquant, indicatif ou à redéfinir. Consigner dans `docs/INDICATEURS_V2.md` (nouvelle section « Repères de calibration »). Aucun code.

**Hors de ce ticket :** modification des indicateurs (01d).

**Attributs :** aucun

**Blocked by:** None.

**Bloque :** 01d, 14a, 18b.

**Status:** livré (06/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 1 h |
| Tests unitaires et comportementaux | 0 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : sources accessibles en ligne ; un repère introuvable est noté « non trouvé ».
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Intégration :** relecture croisée : chaque repère renvoie à un indicateur existant du banc ou à un indicateur à créer

## Acceptance criteria

- [x] 7 repères documentés : source, définition, unité, indicateur correspondant, statut (bloquant, indicatif, à redéfinir) (`docs/INDICATEURS_V2.md`, section 6)
- [x] Écarts de définition entre source et banc listés (section 6, paragraphe « Écarts de définition à traiter au 01d »)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : sans objet (aucun code) ; empreintes inchangées, test `test_two_full_matches_are_reproducible_at_fixed_seed` réussi sur le même code (`a9a74f9`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (voir rapport)

## Rapport d'implémentation (06/11/2026)

**Livré :** `docs/INDICATEURS_V2.md`, nouvelle section 6 « Repères de calibration » : pour chacun des 7 repères, source primaire, population, définition de la source, unité, indicateur du banc, écart de définition et statut ; mesure actuelle du banc pour situer chaque repère ; écarts à traiter au 01d ; limites. Trois lignes existantes corrigées : passes par minute (section 1, dénominateur), haute intensité (section 1, distance ou temps), appels (section 2, source).

**Conclusions :**

| Repère | Statut | Point clé |
|---|---|---|
| R1 tirs par équipe | bloquant | lire `tirs tracés par équipe` ; réel ≈ 13,1 (Premier League 2024-25, calculé) |
| R2 conversion | bloquant, fourchette élargie à 10-12 % | réel ≈ 11,4 % penaltys compris (calculé) |
| R3 buts dans la surface | bloquant | réel 88-89 % (Opta) |
| R4 distance | indicatif | réel 10,2 à 12,0 km par poste (Ligue des champions 2020-21) |
| R5 appels | indicatif | source corrigée (CIES n° 88, SkillCorner) ; option de passe jugée différemment |
| R6 haute intensité | à redéfinir | la source mesure une distance (6 à 10 %), le banc un temps |
| R7 passes par minute | à redéfinir | 15-17 vaut par minute de jeu effectif ; 941 passes par match, soit 10,5 par minute de match |

**Constats non prévus :** la source citée pour les appels (PLOS One 2022) ne contient pas les chiffres ; la cible de 15-17 passes par minute, appliquée au banc depuis le ticket socle 06, mêle deux dénominateurs ; le banc est aujourd'hui proche du réel sur les passes par match (≈ 990) mais loin sur R1 à R6.

**Choix :** fourchette de R2 élargie à 10-12 % et cibles proposées pour R4 (10-12 km), R6 (6-10 % de la distance) et R7 (890-940 passes par match ; 15-17 par minute de jeu effectif) : recommandations, acceptées d'office par le propriétaire (« Tes recommandations et les conseils d'expert sont automatiquement validé »). Aucune constante du jeu n'est touchée.

**Limites :** R1 et R2 calculés à partir de parts publiées ; une seule ligue (Premier League) pour R1, R2, R3, R7 ; aucune donnée publique équivalente trouvée pour la Ligue 1 ; Bradley et al. 2009 en accès payant (seuils vérifiés, distances non relues).

**Tests :** aucun code ; suite complète relancée sur l'arbre du ticket : 2389 passed, 14 deselected, conforme à l'attendu ; relecture croisée : chaque repère renvoie à un indicateur existant du banc (R1 à R5, R7) ou à un indicateur à créer au 01d (R6 distance, R7 par match et par minute de jeu effectif). `CLAUDE.md` : attendu de la suite mis à jour après le 01b (2 389 passés, 14 désélectionnés, sur `a9a74f9`).

**Durée :** estimée 1 h 50 (110 min ; 30/60/0/20), réelle environ 1 h 40 (100 min ; 25/55/0/20). Écart − 9 %.

## Comments

- 06/11/2026, passage 1 : expert APPROVED (empreinte 9627ef8f). Facultatifs, reportés au 01d (qui modifie la même section) : A1 citer la distance totale de chaque poste à côté de sa distance à haute intensité (R6 : 5,8 à 10,3 % selon l'appariement, 5,7 à 9,3 % par bornes croisées) ; A2 nom exact de l'indicateur R4 « km par joueur de champ, par poste ». QC REFUSÉ (ligne 01c absente du registre des estimations), corrigé ; QC VALIDÉ au passage 2. **Clôture VALIDÉ.**
