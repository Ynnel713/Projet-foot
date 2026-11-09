# 06: Catégories de joueurs alignées sur la table des rôles V2

**What to build:** commiter la modification de la colonne « Catégorie » de `data/joueurs.xlsx`, faite à la main par le
propriétaire le 06/11/2026 (12:00) et restée hors du dépôt depuis. Elle aligne le vocabulaire des catégories sur la
table `poste × catégorie` de `v2engine/roles.py` (ticket `v2-realisme/02c`, livré le 06/11/2026).

Aucune ligne de code n'est modifiée par ce ticket. La donnée existe déjà et le ticket vérifie qu'elle est conforme avant
le commit.

**Status:** livré (09/11/2026), validé expert + QC

**Constat (09/11/2026).** `data/joueurs.xlsx` était modifié dans l'arbre de travail depuis le 06/11, sans commit.
- Le code commité dépend déjà de cette version. `v2engine/roles.py` attend « milieu recuperateur », « meneur » et
  « second attaquant », trois noms qui n'existent que dans le classeur modifié.
- Toutes les mesures et suites depuis le 06/11 ont tourné sur ce classeur.
- Un clone propre du dépôt donnait donc un autre moteur que celui mesuré.

**Contenu de la modification** (rapport de comparaison cellule par cellule du 09/11/2026) :
- **Infos principales** : seule la colonne « Catégorie » change, sur 712 cellules. Mêmes 7 474 lignes et mêmes ID dans
  le même ordre ; les 68 autres colonnes, dont les notes et la Moyenne FM, sont identiques.
- **Joueurs avec catégorie** : 1 322 → 906.
- **Catégories retirées** (416 joueurs) : gardien réactif 141, défenseur central constructeur 73, défenseur central
  aérien 69, ailier de jeu 54, stoppeur 41, gardien relayeur 35, libero 3.
- **Catégories renommées** :
  - sentinelle (66) et destructeur (29) → milieu récupérateur ;
  - trequartista (60) et numéro 10 (45) → meneur ;
  - second attaquant mobile ou créatif (61) → second attaquant ;
  - carillero (33) → mezzala.
- **Cas individuels** : un trequartista devient box to box ; un défenseur central aérien devient second attaquant.
- **Description catégories joueurs** : 25 catégories → 11, celles de la table des rôles.
- **Europe, Afrique, Amérique, Asie, Océanie** : deux lignes entièrement vides retirées en fin de feuille ; le reste est
  identique. Les autres feuilles sont identiques.
- **Effet sur le moteur V2** : 95 milieux récupérateurs, 105 meneurs et 62 seconds attaquants portent une catégorie
  reconnue par `roles.py`. Le rôle dédié n'est attribué que si le poste du joueur le prévoit : un « meneur » en MDC ou un
  « second attaquant » en DC garde le rôle par défaut de son poste.
  Les mezzalas passent de 73 à 106 et les box to box de 109 à 110. Les catégories retirées n'avaient pas de rôle dédié
  dans `roles.py` : ces joueurs gardaient déjà le rôle par défaut de leur poste.
- **Effet sur la V1** : aucun sur le jeu. La catégorie n'y sert qu'à l'affichage (note « Style de jeu » de `app.py`, champ
  `categorie` de l'API).

**Décisions du propriétaire**
- 09/11/2026, sur les catégories retirées : « oui c'est voulu. Leur particularité sera dans leurs attributs. Je valide
  toutes mes modifs ». Cela couvre les 416 retraits, les renommages et les deux cas individuels ci-dessus.
- 09/11/2026 : commit séparé par ce ticket, plutôt qu'un revert, sur la recommandation de Claude.

## Critères d'acceptation

- [x] Seule la colonne « Catégorie » d'« Infos principales » change : mêmes en-têtes, mêmes ID dans le même ordre, les
      68 autres colonnes identiques.
- [x] Feuilles hors « Infos principales » et « Description catégories joueurs » identiques, à l'exception des deux
      lignes vides retirées en fin de feuille des cinq continents.
- [x] Chaque catégorie restante est reconnue par `_CATEGORY_ROLE` de `v2engine/roles.py` pour au moins un poste
      (11 catégories). Des différences de casse ou d'espace en fin de nom sont tolérées : `_normalize` les absorbe.
- [x] Retraits et renommages validés par le propriétaire (citation ci-dessus).
- [x] Suite complète verte sur un arbre contenant ce classeur : 2 610 passés, 14 désélectionnés (09/11/2026, 16 min 46 s),
      compte attendu.
- [x] Le commit ne contient que `data/joueurs.xlsx`, ce ticket et le suivi (journal QC, registre des estimations).

**Durée.** Estimée 40 min (analyse 15, rédaction 10, clôture 10, commit 5), confiance élevée. Temps machine hors total :
la suite du 09/11/2026 est reprise, sans nouvelle exécution.

## Comments

**09/11/2026, passage 1.** Expert : `APPROVED` (empreinte `da2d1c32…`). Contrôle qualité : `VALIDÉ` (entrée `1e5c83f2…`). Décision de clôture : **`VALIDÉ`** (« expert APPROVED, QC VALIDÉ »), journalisée.
- Facultatifs de l'expert :
  - A1 : « reçoivent un rôle dédié » remplacé par « portent une catégorie reconnue » (le rôle dépend aussi du poste) ;
  - A2 : le joueur passé de « défenseur central aérien » à « second attaquant » n'a un rôle dédié que si son poste est
    offensif ; changement validé par le propriétaire ;
  - A3 : l'empreinte couvre `data/joueurs.xlsx` ; ticket et suivi entrent au commit comme suivi documentaire.
- Contrôle qualité, réserves non bloquantes :
  - indexer seulement le classeur, ce ticket et le suivi ;
  - `scripts/bench_series.py`, `scripts/measure_v2.py`, `scripts/v2_indicators.py`, `tests/test_v2_indicators.py` et le
    ticket `v2-realisme/06c` ont été modifiés le 09/11/2026 entre 13:13 et 13:19, après la suite de 12:17. Ce travail en
    cours sur le 06c ne fait pas partie de ce ticket : ces fichiers restent hors du commit. La suite a tourné sur l'état
    commité (HEAD et ce classeur).
- Point à surveiller (expert) : les futures séries de mesure V2 partent d'un arbre contenant ce classeur commité.
- **Durée.** Estimée 40 min, réelle environ 45 min (analyse 20, rédaction 10, clôture 10, commit 5), non chronométrée :
  écart de + 13 %.
