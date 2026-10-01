# Scoping de l'enrichissement `preferred_moves` — 01/10/2026

Document de cadrage, pas de code. Fait suite à la décision du
01/10/2026 : un enrichissement de `preferred_moves` sur quasi toute la
base est désormais prévu, ce qui change le statut de GESTE_SIGNATURE de
"scénario mort hors Premier League" à "scénario en attente d'une
dépendance externe". Voir [AUDIT_COUVERTURE_DONNEES_JOUEUR.md](AUDIT_COUVERTURE_DONNEES_JOUEUR.md)
pour le diagnostic complet qui a mené ici.

## 1. Source

**fminside reste la seule source identifiée dans le code existant**
(`scripts/scrape_fminside_attributes.py`, racine du projet). Le verrou
n'est pas sur l'accès au site en général (les attributs numériques FM26
sont déjà scrapés à 93 % sans connexion) — il est spécifique à la section
`section.player-hidden-attributes` qui porte les preferred moves,
inaccessible sans cookie de session fminside valide (`--cookie` /
`FMINSIDE_COOKIE`, voir docstring du script).

Alternatives envisageables, non investiguées en détail (hors périmètre
"document, pas code" de ce tour) :
- **Cookie de compte fminside + relance du scraper existant** — le
  mécanisme est déjà écrit, c'est la voie la moins chère si un compte
  est disponible.
- **Base FM locale (fichier d'édition du jeu Football Manager)** — plus
  fiable et exhaustive si quelqu'un a accès au jeu et à un éditeur de
  base, mais aucun outil d'extraction de ce type n'existe dans ce
  dépôt aujourd'hui ; à construire de zéro.
- **Autre site/API de scouting FM** — non recherché, à évaluer si
  l'option cookie fminside s'avère bloquée en pratique (compte
  limité, rate-limiting agressif sur ~7000 requêtes).

Tu indiques avoir déjà commencé à ajouter des preferred moves à la main
dans le classeur — vérifié : la colonne "Preferred moves" (feuille
"Infos principales") est passée de 362 à **644 joueurs renseignés**
depuis le dernier import en base (+282). C'est une 4ᵉ voie de fait, déjà
en cours : saisie manuelle, en parallèle ou à la place du scraping.

## 2. Vocabulaire — investigation 55 vs 48 close le 01/10/2026

**Correction d'une erreur de ma part** : au tour précédent, j'ai annoncé
un "écart" (`"Moves Ball To Left Foot Before Dribble Attempt"` prétendument
absent de la feuille de référence) en me basant sur une lecture visuelle
tronquée du fichier — erreur de ma part, pas un vrai écart. Vérifié
programmatiquement (`scripts/audit_moves_canoniques.py`, sortie complète
dans `scripts/_audit_moves_out.txt`) : ce move EST bien présent dans la
feuille, à la ligne que j'avais sautée en scannant à l'œil. Je le signale
explicitement plutôt que de laisser la correction se fondre dans le reste.

**Investigation complète, les 3 hypothèses tranchées par lecture de
code, pas par supposition :**

- Le réservoir canonique réel est **`PREFERRED_MOVE_TRANSLATIONS`**
  (`scripts/make_phrase_template.py`) — un dictionnaire de traduction
  anglais→français **maintenu à la main**, 55 entrées. C'est lui qui
  génère la feuille "Preferred moves" du classeur (`_build_preferred_moves_sheet`
  dans le même fichier) — **vérifié que les deux ensembles sont
  identiques, caractère pour caractère** (55 = 55, aucune différence).
- Croisé avec les 56 conditions `preferred_moves` réellement utilisées
  dans les 281 phrases (48 valeurs DISTINCTES, certaines réutilisées
  sur 2 phrases — ex. "Shoots With Power" x2) : **les 48 sont un
  sous-ensemble strict des 55, zéro valeur hors réservoir.** Aucune
  faute de frappe, aucun move inventé.
- **Le "48" n'est donc pas un chiffre erroné ni une référence séparée à
  retrouver** — c'est très probablement le nombre de moves DISTINCTS
  UTILISÉS dans la banque actuelle (48), que tu as gardé en mémoire
  comme "la liste validée", alors que le réservoir DISPONIBLE (55)
  contient 7 moves de plus, simplement non encore exploités par une
  phrase : `Moves Ball To Right Foot Before Dribble Attempt`, `Runs
  With Ball Down Left`, `Runs With Ball Down Right`, `Runs With Ball
  Rarely`, `Tries Killer Balls Often`, `Tries Long Range Passes`, `Uses
  Long Throw To Start Counter Attacks`.

**Conclusion des 3 hypothèses** :
1. *La référence (48) est incomplète, la vraie liste a 55* — reformulée :
   il n'y a jamais eu deux listes concurrentes, juste un réservoir
   disponible (55) et un sous-ensemble utilisé (48). **Pas une
   incomplétude à corriger.**
2. *Le 55ᵉ move est inventé/mal orthographié* — **réfutée**, aucune
   valeur utilisée n'est hors réservoir.
3. *Deux versions FM se télescopent* — **réfutée**, pas de preuve, et
   l'explication plus simple (réservoir vs sous-ensemble utilisé)
   suffit.

**Aucune mise à jour de référence nécessaire** — rien n'était cassé.
Ce qui MANQUAIT réellement, et qui est maintenant en place : un
garde-fou d'import qui aurait détecté le jour où une vraie faute de
frappe serait passée. **Ajouté** dans
`scripts/convert_commentary_xlsx_to_yaml.py::_conditions_for_phrase` —
toute condition `preferred_moves` dont la valeur n'est pas dans
`PREFERRED_MOVE_TRANSLATIONS` fait échouer la conversion (même
mécanisme que `valider_slots` pour les noms de slot). Testé (cas
accepté + cas rejeté), non-régression confirmée : reconvertir les 281
phrases réelles avec ce garde-fou produit un YAML strictement identique
(diff vide).

### Source des 55 — classeur/scraping, PAS un export FM26 vérifié (signalé le 01/10/2026)

Vérifié par lecture directe du commentaire de code au-dessus de
`PREFERRED_MOVE_TRANSLATIONS` (`scripts/make_phrase_template.py`, commit
`8f0142a`, 29/09/2026) : *"Clé = orthographe EXACTE telle que scrapée
(voir scripts/scrape_fminside_attributes.py) — une valeur absente de ce
dictionnaire (base qui évolue) affiche un repli explicite plutôt que de
planter."*

**La source est le scraping fminside sur l'échantillon de joueurs
effectivement récupéré, pas un export ou une documentation officielle
FM26.** Les 55 sont l'ensemble empirique des noms de moves distincts
rencontrés chez les joueurs scrapés avec succès — pas une liste validée
contre le jeu lui-même. Le commentaire du code le reconnaît déjà ("base
qui évolue") et prévoit un repli explicite pour une valeur absente
plutôt qu'un plantage, signe que l'auteur savait ce réservoir incomplet
par construction.

**Risque identifié, non corrigé (je signale, je ne tranche pas)** : le
garde-fou ajouté ce tour protège la cohérence INTERNE (pas de faute de
frappe par rapport à l'existant) mais pas la validité EXTERNE. Si
l'enrichissement en cours fait apparaître un move réellement présent
dans FM26 mais absent des 55 (parce qu'aucun joueur de l'échantillon
initial ne l'avait), le garde-fou le rejettera à tort comme "inconnu" —
un faux positif qui bloquerait une future phrase légitime, pas une vraie
faute de frappe. **Pas d'action proposée ici** : la décision (élargir le
réservoir au fil de l'enrichissement vs. chercher une liste FM26
officielle externe) appartient à l'arbitrage du prochain tour qui
touchera réellement au workstream donnée.

## 3. Granularité

Confirmé par la base : **plusieurs moves par joueur**, pas un seul.
Somme des compteurs de la feuille de référence = 971 occurrences pour
644 joueurs renseignés à ce jour → en moyenne ~1,5 move par joueur
renseigné. Impact sur la sélectivité : une condition `preferred_moves
contient "X"` reste une condition sur UN move précis parmi ceux du
joueur, pas sur l'ensemble de son profil — la sélectivité des phrases
GESTE_SIGNATURE ne change pas de nature avec l'enrichissement, seulement
la PROPORTION de joueurs qui ont une chance d'avoir au moins un move qui
matche une des 31 conditions.

## 4. Cible de couverture : 90 %

Proposition, alignée sur le reste des attributs FM26 déjà en place
(`Aggression`, `Strength`, `Pace`, `Technique`, `Vision` à 93 % ;
`Dribbling`, `Heading`, `Finishing`, `Tackling` à 82 %) — `weak_foot` et
`preferred_moves` sont censés sortir du MÊME passage d'enrichissement
(voir audit précédent : `weak_foot` est déjà à 93 % alors qu'il vient du
même bloc `parse_extras` que `moves`), donc viser le même ordre de
grandeur est cohérent plutôt qu'arbitraire. 95 % me semble optimiste
(les attributs FM26 eux-mêmes plafonnent à 93 %, jamais 100 % sauf
`age`/`fm_rating`) ; 85 % est trop proche du plancher déjà observé pour
les attributs "moyens" (82 %) et laisserait une marge d'échec trop
large. **90 % est le choix qui ne sur-promet ni ne sous-vise.**

## 5. Timeline

Je ne peux pas donner un chiffre engageant sans avoir fait tourner le
scraper — estimation, pas un engagement :
- **Volume restant** : ~6900 joueurs sans `preferred_moves` (7563 - 644
  à ce jour).
- **Débit du scraper** : `--delay` par défaut = 1 s/requête → ~1h55 de
  temps de requête pur pour une passe complète. **Irréaliste comme
  délai réel** : le script documente lui-même un processus de
  correspondance nom/club avec cas AMBIGU/INTROUVABLE/CONFLIT nécessitant
  une relecture manuelle du rapport CSV produit, plus la contrainte
  cookie (expiration de session, relance nécessaire).
- **Estimation réaliste : quelques jours à ~2 semaines**, selon le taux
  d'échec de correspondance réel (inconnu tant que le scraper n'a pas
  tourné à cette échelle) et la disponibilité d'un compte fminside
  stable. Je ne peux pas resserrer cette fourchette sans une première
  passe test à petite échelle (`--limit`).

## 6. Critère de vérification — PRÉALABLE AU DÉMARRAGE (décision du 01/10/2026)

Directive explicite : ce critère doit exister **avant** le lancement du
workstream d'enrichissement, pas après coup — même logique que le
cooldown ("cooldown obligatoire", refus d'import si absent), mais ici en
garde-fou de PROCESSUS plutôt que d'import (voir pourquoi ci-dessous).

**Conception retenue** (à écrire au prochain tour qui touche du code,
pas ce tour-ci) : script de contrôle séparé, sur le modèle de
`scripts/audit_couverture_donnees.py` déjà existant — pas une
modification de `data/import/import_players.py`. Raison du choix :
- L'import des joueurs est une opération d'INFRASTRUCTURE (faire
  rentrer les données en base) ; la cible de 90 % est un objectif
  ÉDITORIAL/PROJET (le workstream est-il fini ou non). Mélanger les deux
  rendrait `import_players.py` responsable d'une décision qui ne lui
  appartient pas — chaque import intermédiaire (ex. après 2000 joueurs
  enrichis sur 6900) ne doit PAS échouer ou alarmer à tort.
- Un script séparé peut tourner à la demande (fin de journée de
  scraping, avant de décider si GESTE_SIGNATURE peut sortir du statut
  PL-only) sans coupler le cycle d'import au cycle de décision projet.

**Forme concrète** : étendre `scripts/audit_couverture_donnees.py`
(déjà capable de calculer `preferred_moves` : X/7563 = Y %) d'un mode
`--seuil 90 --attribut preferred_moves` qui retourne un code de sortie
non-zéro si Y < 90 — utilisable en commande manuelle aujourd'hui, et
automatisable (CI, tâche planifiée) sans changement si le besoin se
confirme. Ce n'est PAS un refus d'import comme le cooldown — c'est un
GO/NO-GO pour décider si la section "PL-only" de `COUVERTURE.md` et la
restriction correspondante du plan V2 peuvent être levées.

## Comportement intermédiaire — TRANCHÉ le 01/10/2026 : Option A

32 phrases GESTE_SIGNATURE sont mortes aujourd'hui sur tout match
hors Premier League (0 des 35 clubs couverts n'étant dans les autres
championnats). **Décision : Option A** (garder en base, documenter
PL-only) — voir [COUVERTURE.md](COUVERTURE.md), section dédiée. Les
trois options sont conservées ci-dessous pour la traçabilité de la
décision, pas comme un choix encore ouvert.

**Option A — Garder en base, documenter "PL-only jusqu'à enrichissement" (RETENUE)**
- *Pour* : rien à retoucher dans `scenarios.yml`/la base, l'info vit
  dans `COUVERTURE.md` (déjà le cas). Le jour où `preferred_moves`
  atteint 90 %, ces phrases redeviennent utilisables sans aucune action.
- *Contre* : `import-seed` reste conforme (pas de "code mort" au sens de
  la règle du projet puisque ces phrases restent potentiellement
  déclenchables, juste rarement) mais un futur import complet du moteur
  simulerait des matchs hors-PL où GESTE_SIGNATURE serait silencieusement
  absent sans que rien ne le signale À L'EXÉCUTION (seule la documentation
  le dit, pas le comportement observé).

**Option B — Retirer temporairement de la banque active (249 phrases), réintégrer après**
- *Pour* : la banque "active" reflète honnêtement ce qui peut
  réellement se déclencher aujourd'hui, pas ce qui existe en texte.
  Repartir de `scenarios.yml` + reconvertir est mécanique (déjà
  comment ce fichier est régénéré, voir `convert_commentary_xlsx_to_yaml.py`).
- *Contre* : retirer puis réintégrer 32 phrases est un aller-retour
  d'édition du classeur/YAML (variante is_active=0 plutôt qu'une
  suppression physique serait plus sûr qu'une suppression-réinsertion),
  et ça complique le diff/l'historique pour un état qui n'est que
  temporaire par construction. Risque d'oubli de réintégration si le
  workstream donnée traîne.

**Option C — Garder sans documenter : exclue**, contraire à la règle
"pas de code mort silencieux" du projet, comme tu l'as toi-même posé.

**Mon inclination (je n'arbitre pas)** : Option A, parce que
`COUVERTURE.md` existe déjà précisément pour porter ce genre d'information
et que la section "VIABILITÉ DES CONDITIONS" ajoutée au tour précédent
couvre déjà ce cas noir sur blanc — B ajoute un cycle d'édition pour un
état transitoire dont la durée réelle (quelques jours à deux semaines,
section 5) ne le justifie pas forcément. Mais si le workstream données
s'annonce plus long que prévu, B devient plus défendable pour éviter
qu'un tableau de bord ou un export analytics compte ces 32 phrases
comme "actives" pendant des mois.
