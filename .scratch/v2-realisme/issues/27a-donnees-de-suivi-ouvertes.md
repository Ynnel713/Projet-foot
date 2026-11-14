# 27a: Données de suivi ouvertes : choix, licence et lecture

**Chantier :** `v2-realisme` (suggestions du propriétaire du 14/11/2026, axe « validation sur données réelles de trajectoires » : sans elle, le moteur peut être cohérent mais faux). **Priorité :** P1 (avant la calibration tactique `v2-collectif/22b`). **Catégorie :** mesure.

**Constat vérifié (14/11/2026) :** le banc compare le moteur à des repères agrégés (tirs, passes, distance parcourue ; `docs/INDICATEURS_V2.md`, ticket 01c). Aucune comparaison à des trajectoires réelles : rien ne dit si la largeur d'un bloc, l'écart entre deux lignes ou la distance au plus proche adversaire à la réception ressemblent au football réel. Aucun jeu de données de suivi n'est présent ni cité dans le dépôt.

**What to build:** choisir au moins un jeu de données de suivi publié en accès libre (candidats à vérifier : échantillon Metrica Sports, données ouvertes SkillCorner, images figées « 360 » des données ouvertes StatsBomb, qui ne donnent que des positions au moment des événements, sans trajectoires continues : ni vitesses ni sprints), vérifier sa licence pour un usage personnel non commercial, son accès réseau depuis l'environnement et son format. Écrire un lecteur (`scripts/`) qui ramène positions des 22 joueurs et du ballon, temps, équipe en possession et événements au repère du moteur (105 × 68 m, sens du jeu). Les données restent hors du dépôt (téléchargées dans un dossier ignoré par git), le lecteur et un petit échantillon de test synthétique y entrent.

**Hors de ce ticket :** distributions de référence (27b) ; comparaison (27c).

**Attributs :** aucun.

**Blocked by:** rien.

**Bloque :** 27b.

**Status:** à faire (choix du jeu de données à proposer au propriétaire avant le code)

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

- [ ] Jeu de données, licence et volume (nombre de matchs, fréquence d'échantillonnage, couverture du terrain) validés par le propriétaire avant le code
- [ ] Aucune donnée téléchargée versionnée dans le dépôt
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme : sortie identique sur deux lectures des mêmes données
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
