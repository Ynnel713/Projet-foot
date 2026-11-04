# Attributs restants : 100 % des caractéristiques exprimées (V2)

Créé le 02/11/2026 à la demande du propriétaire : « vérifier que 100 % des caractéristiques pourront s'exprimer dans le comportement, la taille y compris ».

## Constat (vérifié le 02/11/2026)

`docs/CARTE_ATTRIBUTS_V2.md` décrit bien les 47 attributs + Taille, Pieds, Weak foot, Preferred moves, Postes naturels : **sur le papier, 100 % ont un rôle prévu**. Mais 32 lignes sont « à créer », et les phases qui les portent n'ont **aucun ticket** :

| Phase (PLAN_V2) | Attributs en attente | Ticket existant avant ce chantier |
|---|---|---|
| 7. Centres et jeu aérien | Crossing, Heading, Jumping Reach, Bravery, Long Shots, **Taille** | aucun |
| 8. Ballon hors du terrain | Corners, Free Kick Taking, Long Throws, Penalty Taking | aucun |
| 9. Gardien complet | Aerial Reach, Command of Area, Communication, Kicking, Throwing, Rushing Out, Punching, Eccentricity | aucun |
| 10. Caractère et profil | Weak foot, Pieds, Postes naturels, Preferred moves (hors décision du porteur) | partiel : v2-collectif/19 (Preferred moves comme penchants dans la décision), 21 (Determination, Leadership) |
| « étape duels » (citée par la carte, absente du plan) | Agility, Dribbling, Balance après contact (dérogation A3) | aucun |
| Hors match | Natural Fitness | **non exprimable dans un match isolé** (récupération entre les matchs, D-V09/D-V10) : exception assumée |
| Discipline (contreparties) | Aggression (cartons), Bravery (blessures), gestes Dives Into Tackles, Argues With Officials, Winds Up Opponents | aucun : ni fautes sanctionnées, ni cartons, ni blessures en V2 |

Données (base `data/joueurs.xlsx`, 7 473 lignes) : Taille FM 95,5 %, Weak foot 95,5 %, Postes FM naturels 95,5 %, **Preferred moves 40,3 %**, **Pieds 39,1 %**. 58 gestes préférés distincts.

## Tickets

| # | Titre | Bloqué par |
|---|---|---|
| 01 | Centres, jeu aérien et taille | v2-collectif/18 |
| 02 | Coups de pied arrêtés et ballon hors du terrain | 01 |
| 03 | Gardien complet | 01, 02 |
| 04 | Pied fort, pied faible et postes naturels | v2-collectif/19 |
| 05 | Catalogue des 58 gestes préférés | v2-collectif/19 ; 01-04 pour les gestes concernés |
| 06 | Enrichissement des données (gestes préférés, pied fort) | — |
| 07 | Duels : Agility, Dribbling, Balance après contact, duel un contre un varié et tacle glissé (élargi le 03/11/2026) | — |
| 08 | Garde de couverture : 100 % des caractéristiques branchées | tous les précédents (s'enrichit au fil de l'eau) |
| 09 | Discipline : fautes, cartons, blessures et échauffourées | 02, 07, v2-collectif/29 et 30 |
| 10 | Types de finition (placée, puissante, enroulée, première intention, côté ouvert ou fermé ; lob et dribble du gardien après 03) | v2-collectif/28, 19, 22 ; 03 et 07 pour le lob et le dribble du gardien |
| 11 | Centres variés (enroulé, tendu, en retrait, au ras du sol) | 01, v2-collectif/28, v2-collectif/29 |

## Règle de composition (revue expert A7)

Trois niveaux agissent parfois sur la même décision (tirer de loin, repiquer vers l'axe, se projeter) ; chacun a un rôle unique :

- le **style du coach** déplace un paramètre d'**équipe** (hauteur du bloc, nombre de joueurs projetés, tempo) ;
- l'**état du match** (score, minute) déplace ces mêmes paramètres d'équipe via v2-collectif/21, que le style dose (v2-coach-et-gestion-de-match/02) ;
- le **geste préféré** déplace la **probabilité individuelle** d'un choix (ticket 05) ;
- l'**attribut** règle la **qualité d'exécution** (et la propension seulement quand la carte le lui attribue, ex. Decisions).

Les décalages se multiplient et passent par un **plafond global commun** par décision, pour qu'aucun cumul (Defensif + Stays Back + Work Rate bas) ne rende un comportement impossible ou systématique. À inscrire dans la table de règles de `docs/CARTE_ATTRIBUTS_V2.md` au premier ticket qui en a besoin.
