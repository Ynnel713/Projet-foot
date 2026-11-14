# 27a: Données de suivi ouvertes : choix, licence et lecture

**Chantier :** `v2-realisme` (suggestions du propriétaire du 14/11/2026, axe « validation sur données réelles de trajectoires » : sans elle, le moteur peut être cohérent mais faux). **Priorité :** P1 (avant la calibration tactique `v2-collectif/22b`). **Catégorie :** mesure.

**Constat vérifié (14/11/2026) :** le banc compare le moteur à des repères agrégés (tirs, passes, distance parcourue ; `docs/INDICATEURS_V2.md`, ticket 01c). Aucune comparaison à des trajectoires réelles : rien ne dit si la largeur d'un bloc, l'écart entre deux lignes ou la distance au plus proche adversaire à la réception ressemblent au football réel. Aucun jeu de données de suivi n'est présent ni cité dans le dépôt.

**What to build:** choisir au moins un jeu de données de suivi publié en accès libre (candidats à vérifier : échantillon Metrica Sports, données ouvertes SkillCorner, images figées « 360 » des données ouvertes StatsBomb, qui ne donnent que des positions au moment des événements, sans trajectoires continues : ni vitesses ni sprints), vérifier sa licence pour un usage personnel non commercial, son accès réseau depuis l'environnement et son format. Écrire un lecteur (`scripts/`) qui ramène positions des 22 joueurs et du ballon, temps, équipe en possession et événements au repère du moteur (105 × 68 m, sens du jeu). Les données restent hors du dépôt (téléchargées dans un dossier ignoré par git), le lecteur et un petit échantillon de test synthétique y entrent.

**Hors de ce ticket :** distributions de référence (27b) ; comparaison (27c).

**Attributs :** aucun.

**Blocked by:** rien.

**Bloque :** 27b.

**Status:** implémenté (14/11/2026) — en attente de /valider-ticket-simulafoot

## Estimation

| Poste | Durée |
|---|---|
| Analyse (jeux de données, licences, formats) | 40 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : faible. Hypothèses : au moins un jeu de données accessible par le réseau de l'environnement et utilisable à titre personnel ; sinon le ticket se termine sur un rapport « non trouvé » et 27b à 27c sont suspendus.
Temps machine, non compté : téléchargement.

## Tests

- **Unitaires :** lecteur sur un échantillon synthétique : changement de repère, sens du jeu, équipe en possession.

## Acceptance criteria

- [x] Jeu de données, licence et volume (nombre de matchs, fréquence d'échantillonnage, couverture du terrain) validés par le propriétaire avant le code
- [x] Aucune donnée téléchargée versionnée dans le dépôt (`data/externe/` dans `.gitignore`)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme : sortie identique sur deux lectures des mêmes données
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 971 passés, 14 désélectionnés : 2 962 + 9 tests du lecteur ; attendu de `CLAUDE.md` mis à jour)

## Implémentation (14/11/2026)

**Décisions du propriétaire (14/11/2026, « Ok » sur la présentation) :** SkillCorner en source principale, Metrica en contrôle des vitesses ; mètres réels gardés (terrains non standard signalés) ; données dans `data/externe/`, ignoré par git.

**Critères chiffrés posés avant le code :** tous les matchs lus sans erreur, avec leur volume ; test synthétique du repère (centre (0, 0) → (52,5 ; 34), rotation en deuxième période) ; empreintes sha256 vérifiées ; aucune donnée versionnée ; deux lectures identiques ; lecture d'un match en moins de 60 s ; suite complète comparée à l'attendu.

**Code :** `scripts/suivi_reel.py` (téléchargement idempotent et vérifié, `read_skillcorner`, `read_metrica`, `to_engine`, `summary`, commandes `telecharger` et `resume`) ; tests `tests/test_suivi_reel.py` (9, données synthétiques, sans réseau) ; `.gitignore` (`data/externe/`).

**Mesures :** `docs/INDICATEURS_V2.md`, section 38. 20 matchs SkillCorner (le README en annonce 10) et 2 Metrica lus sans erreur, 2,0 à 6,4 s par match ; deux lectures identiques ; second téléchargement en 11 s sans transfert. Constats : 10 terrains SkillCorner sur 20 hors 105 × 68 m ; au moins 20 joueurs détectés sur 0,7 à 11,2 % des images SkillCorner seulement (positions estimées hors caméra), ce qui oriente les mesures du 27b.

**Limites acceptées (réserve A3 de l'expert) :** Metrica ne donne ni l'équipe en possession ni la phase (fichiers d'événements non lus : source cantonnée au contrôle des vitesses par le propriétaire) ; SkillCorner : phases de jeu lues, événements dynamiques non lus. Le 27b lira les événements s'il en a besoin.

**Durée :** estimée 1 h 55 (40/40/20/15), réelle environ 1 h 50 (40/35/15/20), à l'horloge de la session hors attentes machine (téléchargement de 1,9 Go, suite complète).

## Comments

- 14/11/2026, passage 1 : expert REJECTED. A1 (bloquant) : largeur du terrain en miroir par rapport au moteur (y du moteur vers le bas, `formation.py`) ; corrigé dans `to_engine` (`W/2 − s·y`), tests de côté ajoutés, côtés vérifiés sur 3 matchs réels. A2 (réserve) : temps SkillCorner remis à 0 par période, comme Metrica. A3 (réserve) : limites de possession et d'événements consignées ci-dessus. A4 (facultatif) : nombre de matchs listés journalisé au téléchargement.
