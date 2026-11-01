# Journal — ticket 04 : lot 1, avant-centres des 5 grands championnats (01/11/2026)

Sauvegarde avant écriture : `data/joueurs_backup_20261101_014409.xlsx` (`cmp` identique à l'état de `ca5920a`).

Méthode (validée le 31/10/2026, « Oui, tout ») : x' = clip(round(x·(1+λ·c_cat)), 5, 99) sur les attributs de poids > 0 du poste noté ; coefficients c_cat par profil (neutre 1/1/1/1/1 ; déclin technique 0,4, mental 0,15, physique 1, CPA 0,4, gardien 0,6 ; progression 1/0,8/0,5/0,5/1) ; λ minimal atteignant la cible, résolu conjointement (Gauss-Seidel, 3 itérations). Profil : déclin si baisse et âge ≥ 30, progression si hausse et âge ≤ 23, neutre sinon.

## Moyennes FM

| Joueur | Âge | Avant | Après | Profil | Justification (résumé) |
|---|---|---|---|---|---|
| Donyell Malen | 27 | 77 | 82 | neutre | ~20 buts depuis janvier 2026 (15 à la Roma) ; 6 buts en 5 matchs de Serie A 2026-27. Fiabilité élevée. |
| Olivier Giroud | 39 | 82 | 76 | déclin | 2 buts en 7 matchs de L1 2026-27 à Lille ; 82 le plaçait au niveau de Ferran Torres. Fiabilité moyenne. |
| Iago Aspas | 39 | 81 | 76 | déclin | 4 buts en Liga 2025-26 ; 1 but en 220 min en 2026-27 puis blessure. Fiabilité moyenne. |
| Omar Marmoush | 27 | 84 | 80 | neutre | Peu utilisé à City en 2025-26 ; 0 but, 0 passe en prêt à Tottenham. Fiabilité moyenne. |
| Victor Boniface | 25 | 76 | 72 | neutre | 0 but en 11 matchs (prêt Werder 2025-26) ; 5 minutes en 2026-27. Fiabilité moyenne. |
| Artem Dovbyk | 29 | 77 | 74 | neutre | 3 buts en 18 matchs en 2025-26, blessures ; aucun but confirmé à Bologne. Fiabilité faible. |
| Santiago Castro | 21 | 81 | 78 | neutre | Remplaçant de Malen à la Roma, 1 but en 6 matchs ; 81 = niveau de Gouiri. Fiabilité moyenne. |
| Richarlison | 29 | 73 | 76 | neutre | 11 buts et 4 passes en Premier League 2025-26 ; hausse modérée (écarté de la liste PL cet été). Fiabilité moyenne. |
| Robert Lewandowski | 38 | 78 | 78 | déclin | Cas test 03 réappliqué avec la méthode par catégorie (note inchangée). |
| Lennart Karl | 18 | 79 | 79 | progression | Idem. |
| Paris Brunner | 20 | 72 | 72 | progression | Idem. |
| Luka Modrić | 40 | 81 | 81 | déclin | Idem. |
| Declan Rice | — | 87 | 87 | — | Témoin, non modifié. |
| Loïs Openda | 26 | 77 | 77 | — | Correction 77 → 74 proposée puis retirée par le propriétaire (« cela me semble sévère pour openda »). À réévaluer après ~15 matchs avec Lyon. |

Notes maintenues après examen (14) : Kane 87, Gyökeres 82, Thuram 86, Watkins 80, Dybala 84, Undav 83, Schick 82, Budimir 80,5, Balogun 75, Aubameyang 79,5, Gerard Moreno 79, Kramarić 80, Pio Esposito 80, Welbeck 80 (avant effet de rang, voir plus bas).

Sources consultées le 31/10/2026 (recherche web) : FotMob, FBref, Transfermarkt, Sofascore, Maxifoot, sites des ligues. Saison 2026-27 à ~10 journées : les écarts reposent d'abord sur 2025-26.

## Effet de rang (autres joueurs déplacés)

21 joueurs bougent, de 0,5 à 1 point (aucun attribut modifié) :
- Wout Weghorst : 76 → 77
- Raúl Jiménez : 76 → 77
- Marcus Rashford : 80 → 81
- Gianluca Scamacca : 80 → 81
- Francisco Trincão : 83 → 84
- Désiré Doué : 81 → 82
- Darwin Núñez : 79 → 80
- Bradley Barcola : 81 → 82
- Antoine Semenyo : 80 → 81
- Terem Moffi : 74 → 74.5
- Riccardo Orsolini : 82 → 82.5
- Pierre-Emerick Aubameyang : 79.5 → 80
- Michael Gregoritsch : 74 → 74.5
- Mattia Zaccagni : 82.5 → 83
- Mateo Pellegrino : 76.5 → 77
- Kaio Jorge : 78 → 78.5
- Hee-chan Hwang : 74 → 74.5
- Gerard Moreno : 79 → 79.5
- Eldor Shomurodov : 74 → 74.5
- Ante Budimir : 80.5 → 81
- Ange-Yoan Bonny : 78 → 78.5

Parmi eux, trois notes « maintenues » du lot gagnent 0,5 : Aubameyang 79,5 → 80, Gerard Moreno 79 → 79,5, Budimir 80,5 → 81.

## Sélections nationales (régénérées)

| Sélection | Sort | Entre | Cause |
|---|---|---|---|
| Espagne | Iago Aspas | Alberto Moleiro | baisse d'Aspas |
| France | Olivier Giroud | Désiré Doué | baisse de Giroud (+ Doué 81 → 82) |
| Italie | Matteo Politano | Gianluca Scamacca | Scamacca 80 → 81 par effet de rang |
| Nigeria | Victor Boniface | Chidera Ejuke | baisse de Boniface |
| Pays-Bas | Arnaut Danjuma | Donyell Malen | hausse de Malen |

## Attributs modifiés (avant → après)

Pour les 4 cas test, « Avant » est l'attribut d'origine (avant le ticket 03) : la méthode par catégorie est appliquée depuis l'origine, sans double correction. Les attributs de poids 0 pour le poste (ex. Long Throws) ne sont pas touchés.

### Robert Lewandowski (poste noté BU, profil déclin, λ -0.1670)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 45 | 42 |
| Dribbling | 65 | 61 |
| Finishing | 90 | 84 |
| First Touch | 80 | 75 |
| Heading | 85 | 79 |
| Long Shots | 60 | 56 |
| Marking | 35 | 33 |
| Passing | 65 | 61 |
| Tackling | 35 | 33 |
| Technique | 80 | 75 |
| Aggression | 65 | 63 |
| Anticipation | 80 | 78 |
| Bravery | 75 | 73 |
| Composure | 85 | 83 |
| Concentration | 80 | 78 |
| Decisions | 85 | 83 |
| Determination | 90 | 88 |
| Flair | 70 | 68 |
| Leadership | 75 | 73 |
| Off the Ball | 85 | 83 |
| Positioning | 35 | 34 |
| Teamwork | 65 | 63 |
| Vision | 70 | 68 |
| Work Rate | 65 | 63 |
| Acceleration | 55 | 46 |
| Agility | 55 | 46 |
| Balance | 80 | 67 |
| Jumping Reach | 65 | 54 |
| Natural Fitness | 85 | 71 |
| Pace | 55 | 46 |
| Stamina | 65 | 54 |
| Strength | 75 | 62 |
| Free Kick Taking | 75 | 70 |
| Penalty Taking | 90 | 84 |

### Donyell Malen (poste noté BU, profil neutre, λ +0.0645)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 60 | 64 |
| Dribbling | 75 | 80 |
| Finishing | 75 | 80 |
| First Touch | 65 | 69 |
| Heading | 60 | 64 |
| Long Shots | 65 | 69 |
| Marking | 30 | 32 |
| Passing | 60 | 64 |
| Tackling | 30 | 32 |
| Technique | 70 | 75 |
| Aggression | 55 | 59 |
| Anticipation | 70 | 75 |
| Bravery | 45 | 48 |
| Composure | 65 | 69 |
| Concentration | 50 | 53 |
| Decisions | 55 | 59 |
| Determination | 65 | 69 |
| Flair | 70 | 75 |
| Leadership | 35 | 37 |
| Off the Ball | 70 | 75 |
| Positioning | 30 | 32 |
| Teamwork | 55 | 59 |
| Vision | 60 | 64 |
| Work Rate | 65 | 69 |
| Acceleration | 80 | 85 |
| Agility | 80 | 85 |
| Balance | 65 | 69 |
| Jumping Reach | 50 | 53 |
| Natural Fitness | 65 | 69 |
| Pace | 80 | 85 |
| Stamina | 65 | 69 |
| Strength | 65 | 69 |
| Free Kick Taking | 55 | 59 |
| Penalty Taking | 65 | 69 |

### Lennart Karl (poste noté MOC, profil progression, λ +0.0565)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 60 | 63 |
| Dribbling | 80 | 85 |
| Finishing | 60 | 63 |
| First Touch | 80 | 85 |
| Heading | 30 | 32 |
| Long Shots | 80 | 85 |
| Marking | 30 | 32 |
| Passing | 65 | 69 |
| Tackling | 30 | 32 |
| Technique | 80 | 85 |
| Aggression | 35 | 37 |
| Anticipation | 60 | 63 |
| Bravery | 40 | 42 |
| Composure | 60 | 63 |
| Concentration | 50 | 52 |
| Decisions | 60 | 63 |
| Determination | 65 | 68 |
| Flair | 80 | 84 |
| Leadership | 25 | 26 |
| Off the Ball | 60 | 63 |
| Positioning | 30 | 31 |
| Teamwork | 60 | 63 |
| Vision | 65 | 68 |
| Work Rate | 55 | 57 |
| Acceleration | 75 | 77 |
| Agility | 80 | 82 |
| Balance | 60 | 62 |
| Jumping Reach | 25 | 26 |
| Natural Fitness | 60 | 62 |
| Pace | 60 | 62 |
| Stamina | 70 | 72 |
| Strength | 30 | 31 |
| Corners | 65 | 67 |
| Free Kick Taking | 75 | 77 |
| Penalty Taking | 75 | 77 |

### Artem Dovbyk (poste noté BU, profil neutre, λ -0.0455)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 40 | 38 |
| Dribbling | 55 | 52 |
| Finishing | 80 | 76 |
| First Touch | 65 | 62 |
| Heading | 80 | 76 |
| Long Shots | 55 | 52 |
| Marking | 30 | 29 |
| Passing | 50 | 48 |
| Tackling | 40 | 38 |
| Technique | 60 | 57 |
| Aggression | 60 | 57 |
| Anticipation | 70 | 67 |
| Bravery | 60 | 57 |
| Composure | 60 | 57 |
| Concentration | 70 | 67 |
| Decisions | 65 | 62 |
| Determination | 75 | 72 |
| Flair | 60 | 57 |
| Leadership | 50 | 48 |
| Off the Ball | 60 | 57 |
| Positioning | 40 | 38 |
| Teamwork | 75 | 72 |
| Vision | 60 | 57 |
| Work Rate | 75 | 72 |
| Acceleration | 70 | 67 |
| Agility | 55 | 52 |
| Balance | 75 | 72 |
| Jumping Reach | 80 | 76 |
| Natural Fitness | 75 | 72 |
| Pace | 75 | 72 |
| Stamina | 75 | 72 |
| Strength | 80 | 76 |
| Free Kick Taking | 50 | 48 |
| Penalty Taking | 75 | 72 |

### Victor Boniface (poste noté BU, profil neutre, λ -0.0540)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 40 | 38 |
| Dribbling | 80 | 76 |
| Finishing | 65 | 61 |
| First Touch | 75 | 71 |
| Heading | 70 | 66 |
| Long Shots | 65 | 61 |
| Marking | 20 | 19 |
| Passing | 65 | 61 |
| Tackling | 25 | 24 |
| Technique | 80 | 76 |
| Aggression | 65 | 61 |
| Anticipation | 70 | 66 |
| Bravery | 65 | 61 |
| Composure | 60 | 57 |
| Concentration | 60 | 57 |
| Decisions | 65 | 61 |
| Determination | 80 | 76 |
| Flair | 85 | 80 |
| Leadership | 40 | 38 |
| Off the Ball | 60 | 57 |
| Positioning | 25 | 24 |
| Teamwork | 50 | 47 |
| Vision | 65 | 61 |
| Work Rate | 45 | 43 |
| Acceleration | 60 | 57 |
| Agility | 70 | 66 |
| Balance | 80 | 76 |
| Jumping Reach | 75 | 71 |
| Natural Fitness | 25 | 24 |
| Pace | 65 | 61 |
| Stamina | 50 | 47 |
| Strength | 85 | 80 |
| Free Kick Taking | 50 | 47 |
| Penalty Taking | 75 | 71 |

### Omar Marmoush (poste noté AG, profil neutre, λ -0.0540)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 60 | 57 |
| Dribbling | 80 | 76 |
| Finishing | 70 | 66 |
| First Touch | 70 | 66 |
| Heading | 55 | 52 |
| Long Shots | 70 | 66 |
| Marking | 35 | 33 |
| Passing | 65 | 61 |
| Tackling | 40 | 38 |
| Technique | 75 | 71 |
| Aggression | 65 | 61 |
| Anticipation | 80 | 76 |
| Bravery | 55 | 52 |
| Composure | 80 | 76 |
| Concentration | 65 | 61 |
| Decisions | 70 | 66 |
| Determination | 80 | 76 |
| Flair | 80 | 76 |
| Leadership | 60 | 57 |
| Off the Ball | 80 | 76 |
| Positioning | 35 | 33 |
| Teamwork | 65 | 61 |
| Vision | 75 | 71 |
| Work Rate | 75 | 71 |
| Acceleration | 80 | 76 |
| Agility | 80 | 76 |
| Balance | 75 | 71 |
| Jumping Reach | 55 | 52 |
| Natural Fitness | 70 | 66 |
| Pace | 80 | 76 |
| Stamina | 65 | 61 |
| Strength | 65 | 61 |
| Corners | 75 | 71 |
| Free Kick Taking | 90 | 85 |
| Penalty Taking | 80 | 76 |

### Richarlison (poste noté BU, profil neutre, λ +0.0360)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 55 | 57 |
| Dribbling | 55 | 57 |
| Finishing | 65 | 67 |
| First Touch | 50 | 52 |
| Heading | 85 | 88 |
| Long Shots | 55 | 57 |
| Marking | 30 | 31 |
| Passing | 55 | 57 |
| Tackling | 60 | 62 |
| Technique | 65 | 67 |
| Aggression | 75 | 78 |
| Anticipation | 60 | 62 |
| Bravery | 80 | 83 |
| Composure | 50 | 52 |
| Concentration | 60 | 62 |
| Decisions | 50 | 52 |
| Determination | 70 | 73 |
| Flair | 70 | 73 |
| Leadership | 45 | 47 |
| Off the Ball | 50 | 52 |
| Positioning | 50 | 52 |
| Teamwork | 65 | 67 |
| Vision | 50 | 52 |
| Work Rate | 80 | 83 |
| Acceleration | 75 | 78 |
| Agility | 70 | 73 |
| Balance | 60 | 62 |
| Jumping Reach | 55 | 57 |
| Natural Fitness | 55 | 57 |
| Pace | 75 | 78 |
| Stamina | 80 | 83 |
| Strength | 65 | 67 |
| Free Kick Taking | 45 | 47 |
| Penalty Taking | 60 | 62 |

### Iago Aspas (poste noté BU, profil déclin, λ -0.1365)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 60 | 57 |
| Dribbling | 75 | 71 |
| Finishing | 80 | 76 |
| First Touch | 75 | 71 |
| Heading | 65 | 61 |
| Long Shots | 75 | 71 |
| Marking | 25 | 24 |
| Passing | 75 | 71 |
| Tackling | 30 | 28 |
| Technique | 80 | 76 |
| Aggression | 60 | 59 |
| Anticipation | 80 | 78 |
| Bravery | 80 | 78 |
| Composure | 80 | 78 |
| Concentration | 75 | 73 |
| Decisions | 80 | 78 |
| Determination | 75 | 73 |
| Flair | 85 | 83 |
| Leadership | 95 | 93 |
| Off the Ball | 85 | 83 |
| Positioning | 40 | 39 |
| Teamwork | 80 | 78 |
| Vision | 75 | 73 |
| Work Rate | 80 | 78 |
| Acceleration | 55 | 47 |
| Agility | 60 | 52 |
| Balance | 75 | 65 |
| Jumping Reach | 55 | 47 |
| Natural Fitness | 70 | 60 |
| Pace | 55 | 47 |
| Stamina | 35 | 30 |
| Strength | 35 | 30 |
| Free Kick Taking | 75 | 71 |
| Penalty Taking | 80 | 76 |

### Santiago Castro (poste noté BU, profil neutre, λ -0.0335)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 65 | 63 |
| Dribbling | 65 | 63 |
| Finishing | 65 | 63 |
| First Touch | 65 | 63 |
| Heading | 70 | 68 |
| Long Shots | 80 | 77 |
| Marking | 40 | 39 |
| Passing | 70 | 68 |
| Tackling | 50 | 48 |
| Technique | 70 | 68 |
| Aggression | 90 | 87 |
| Anticipation | 80 | 77 |
| Bravery | 80 | 77 |
| Composure | 60 | 58 |
| Concentration | 70 | 68 |
| Decisions | 65 | 63 |
| Determination | 90 | 87 |
| Flair | 70 | 68 |
| Leadership | 55 | 53 |
| Off the Ball | 75 | 72 |
| Positioning | 50 | 48 |
| Teamwork | 70 | 68 |
| Vision | 70 | 68 |
| Work Rate | 90 | 87 |
| Acceleration | 70 | 68 |
| Agility | 65 | 63 |
| Balance | 75 | 72 |
| Jumping Reach | 70 | 68 |
| Natural Fitness | 65 | 63 |
| Pace | 65 | 63 |
| Stamina | 75 | 72 |
| Strength | 70 | 68 |
| Free Kick Taking | 50 | 48 |
| Penalty Taking | 60 | 58 |

### Paris Brunner (poste noté BU, profil progression, λ +0.1000)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 45 | 50 |
| Dribbling | 70 | 77 |
| Finishing | 65 | 72 |
| First Touch | 60 | 66 |
| Heading | 55 | 61 |
| Long Shots | 60 | 66 |
| Marking | 15 | 16 |
| Passing | 50 | 55 |
| Tackling | 20 | 22 |
| Technique | 65 | 72 |
| Aggression | 65 | 70 |
| Anticipation | 50 | 54 |
| Bravery | 40 | 43 |
| Composure | 45 | 49 |
| Concentration | 40 | 43 |
| Decisions | 45 | 49 |
| Determination | 70 | 76 |
| Flair | 75 | 81 |
| Leadership | 50 | 54 |
| Off the Ball | 60 | 65 |
| Positioning | 15 | 16 |
| Teamwork | 45 | 49 |
| Vision | 55 | 59 |
| Work Rate | 60 | 65 |
| Acceleration | 65 | 68 |
| Agility | 65 | 68 |
| Balance | 60 | 63 |
| Jumping Reach | 60 | 63 |
| Natural Fitness | 65 | 68 |
| Pace | 65 | 68 |
| Stamina | 55 | 58 |
| Strength | 55 | 58 |
| Free Kick Taking | 50 | 52 |
| Penalty Taking | 80 | 84 |

### Luka Modrić (poste noté MC, profil déclin, λ -0.1430)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 75 | 71 |
| Dribbling | 80 | 75 |
| Finishing | 55 | 52 |
| First Touch | 99 | 93 |
| Heading | 35 | 33 |
| Long Shots | 65 | 61 |
| Marking | 40 | 38 |
| Passing | 90 | 85 |
| Tackling | 45 | 42 |
| Technique | 95 | 90 |
| Aggression | 60 | 59 |
| Anticipation | 80 | 78 |
| Bravery | 70 | 68 |
| Composure | 90 | 88 |
| Concentration | 90 | 88 |
| Decisions | 90 | 88 |
| Determination | 85 | 83 |
| Flair | 75 | 73 |
| Leadership | 80 | 78 |
| Off the Ball | 80 | 78 |
| Positioning | 75 | 73 |
| Teamwork | 80 | 78 |
| Vision | 95 | 93 |
| Work Rate | 70 | 68 |
| Acceleration | 60 | 51 |
| Agility | 65 | 56 |
| Balance | 70 | 60 |
| Jumping Reach | 30 | 26 |
| Natural Fitness | 80 | 69 |
| Pace | 55 | 47 |
| Stamina | 55 | 47 |
| Strength | 40 | 34 |
| Corners | 80 | 75 |
| Free Kick Taking | 65 | 61 |

### Olivier Giroud (poste noté BU, profil déclin, λ -0.1500)

| Attribut | Avant | Après |
|---|---|---|
| Crossing | 35 | 33 |
| Dribbling | 55 | 52 |
| Finishing | 80 | 75 |
| First Touch | 70 | 66 |
| Heading | 90 | 85 |
| Long Shots | 55 | 52 |
| Marking | 40 | 38 |
| Passing | 60 | 56 |
| Tackling | 40 | 38 |
| Technique | 65 | 61 |
| Aggression | 70 | 68 |
| Anticipation | 80 | 78 |
| Bravery | 85 | 83 |
| Composure | 80 | 78 |
| Concentration | 85 | 83 |
| Decisions | 75 | 73 |
| Determination | 99 | 97 |
| Flair | 65 | 64 |
| Leadership | 80 | 78 |
| Off the Ball | 80 | 78 |
| Positioning | 40 | 39 |
| Teamwork | 90 | 88 |
| Vision | 65 | 64 |
| Work Rate | 60 | 59 |
| Acceleration | 45 | 38 |
| Agility | 60 | 51 |
| Balance | 90 | 76 |
| Jumping Reach | 90 | 76 |
| Natural Fitness | 80 | 68 |
| Pace | 50 | 42 |
| Stamina | 55 | 47 |
| Strength | 80 | 68 |
| Free Kick Taking | 55 | 52 |
| Penalty Taking | 85 | 80 |

