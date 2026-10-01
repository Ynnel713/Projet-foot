# Plan V2 éditoriale — de 281 à ~700-800 phrases

Livrable de planification uniquement — **aucun code, aucune phrase écrite
dans ce document**. Fait suite à l'import du 30/09/2026 (voir
[COUVERTURE.md](COUVERTURE.md)) et au smoke test du même jour (voir
`scripts/smoke_test_pipeline.py` et son rapport).

## PRÉREQUIS DONNÉES — mis à jour le 01/10/2026

Section créée le 30/09/2026, révisée le 01/10/2026 suite à la décision
d'enrichir `preferred_moves` sur quasi toute la base (cible 90 %, voir
[ENRICHISSEMENT_PREFERRED_MOVES.md](ENRICHISSEMENT_PREFERRED_MOVES.md)).
**`preferred_moves` n'est plus listé comme attribut "à risque" ci-dessous**
— il est traité comme un attribut pleinement viable à terme, sous réserve
que la cible de couverture soit atteinte (voir "Dépendances externes").
`height_cm` et `foot` restent à risque, sans dépendance d'enrichissement
planifiée à ce jour.

### Attributs nécessaires par nouveau scénario (Tier 1) et leur couverture réelle

| Scénario | Attributs cités dans les conditions types de la fiche | Couverture réelle (7563 joueurs) | Fiche impactée ? |
|---|---|---|---|
| DÉFENSE | `Tackling` (82 %), `Pace` (93 %), `height_cm` (**11,7 %**) | Mixte | **Oui** — l'exemple "dégagement aérien, height_cm >= 190" hérite du même risque que BUT/SURNOM "Le colosse" (0,73 % réel) |
| CORNER | `Heading` (82 %) + `height_cm` (**11,7 %**), `Strength` (93 %), `Technique` (93 %) | Mixte | **Oui** — même combo Heading+height_cm que ci-dessus |
| FAUTE_SIMPLE | `Aggression` (93 %), `Tackling` (82 %), `minute` (100 %, contexte) | Viable | Non |
| TIR_NON_CADRÉ | `Finishing` (82 %), `preferred_moves` (en cours d'enrichissement, cible 90 %) | Viable sous réserve de la cible | Non — plus de restriction particulière sur `preferred_moves` une fois la cible atteinte |
| CARTON_JAUNE | `Aggression` (93 %), `preferred_moves` (en cours d'enrichissement, cible 90 %), `minute` | Viable sous réserve de la cible | Non — idem |
| REMPLACEMENT | `age` (100 %), `minute`, `fm_rating` (**100 %**, vérifié) | Viable | Non |

**Tier 2/3** (HORS-JEU, MI_TEMPS_FIN_MATCH, BLESSURE, AMBIANCE,
STATISTIQUES_PÉRIODIQUES, VAR) : aucun n'utilise `height_cm` dans les
conditions types proposées — pas de risque donnée identifié pour ces 6
fiches. AMBIANCE et VAR n'ont même quasiment aucune condition Player
(contexte de match uniquement), donc aucun risque par construction.

### Action préalable par attribut

| Attribut | Couverture | Action préalable | Impact volume |
|---|---|---|---|
| `preferred_moves` | 4,8 % → **cible 90 %** (enrichissement planifié, voir Dépendances externes) | Suivre l'avancement de l'enrichissement — pas de restriction d'écriture une fois la cible atteinte | Aucun — TIR_NON_CADRÉ/CARTON_JAUNE peuvent utiliser `preferred_moves` sans précaution particulière dès que la cible est confirmée |
| `height_cm` | 11,7 % | Cause identifiée (nom de colonne Excel divergent entre le scraper et l'import, voir AUDIT_COUVERTURE_DONNEES_JOUEUR.md) — correctif possible mais non appliqué (661 conflits de valeur à arbitrer d'abord). **Pas d'enrichissement planifié à ce jour.** | DÉFENSE et CORNER perdent leurs exemples "dégagement/tête" tels quels tant que non résolu |
| `foot` | 39,1 % | Partiel, viable pour un usage ponctuel (1 phrase existante) mais pas pour un scénario qui en ferait un pilier | Aucune fiche v2 n'en dépend actuellement |
| `Aggression`, `Pace`, `Strength`, `Technique`, `Vision` | 93 % | Aucune action — viable tel quel | — |
| `Dribbling`, `Heading`, `Finishing`, `Tackling` | 82 % | Aucune action — viable tel quel | — |
| `age`, `fm_rating` | 100 % | Aucune action — viable tel quel | — |
| `weak_foot` | 93 % | Aucune action — viable tel quel | — |

### Dépendances externes

**L'enrichissement `preferred_moves` est un prérequis de livraison V2,
pas un détail technique** — sa timeline conditionne la livraison des
phrases GESTE_SIGNATURE (existantes, 32/37 aujourd'hui PL-only) et de
toute nouvelle phrase V2 qui s'appuierait sur cet attribut sans
restriction.

- **Cible de couverture** : 90 % des 7563 joueurs (voir justification
  dans ENRICHISSEMENT_PREFERRED_MOVES.md, section 4).
- **Source** : scraping fminside (cookie de session requis) et/ou saisie
  manuelle déjà en cours côté utilisateur (644/7563 à ce jour, +282
  depuis le dernier import).
- **Timeline estimée** : quelques jours à ~2 semaines (non engageante,
  dépend du taux d'échec de correspondance du scraper, voir section 5
  du même fichier).
- **Critère de vérification** : contrôle de couverture à spécifier
  (proposition : audit automatisé rejoué après chaque import, pas un
  refus bloquant d'import contrairement au cooldown — voir section 6).
- **Comportement intermédiaire** (avant que la cible soit atteinte) :
  trois options présentées et non tranchées dans
  ENRICHISSEMENT_PREFERRED_MOVES.md — garder en base documenté PL-only
  (A), retirer temporairement de la banque active (B), ou garder sans
  documenter (C, exclu).
- **Garde-fou complémentaire** : cascade de variantes au niveau du
  sélecteur (DEFAUT → SURNOM si 0 candidat), formalisée dans le
  docstring de `engine/phrase_selector.py` (étape 7) — absorbe une
  partie du risque si l'enrichissement prend du retard, sans attendre
  la cible de 90 % pour limiter la casse.

**Pas de changement de volume ni de cooldown dans ce document** — les
chiffres des 12 fiches plus bas restent ceux du tour précédent.

---

## Constat transversal trouvé par le smoke test (historique — statut dépassé par la décision d'enrichissement du 01/10/2026, voir "Dépendances externes" ci-dessus)

Conservé tel quel pour la traçabilité de la décision, mais **ne plus lire
"preferred_moves à 4,8 %" comme un verdict définitif** : un enrichissement
est désormais planifié (cible 90 %), ce qui change GESTE_SIGNATURE de
"scénario mort hors Premier League" à "scénario en attente d'une
dépendance externe".

Le smoke test a fait échouer GESTE_SIGNATURE sur 2 de ses 4 occurrences
(0 phrase sélectionnable). Cause creusée : **seulement 4,8 % des 7563
joueurs importés (362) ont un `preferred_moves` renseigné** — colonne
source majoritairement vide dans le classeur `joueurs.xlsx`, pas un défaut
du moteur. Or **56 des 281 phrases (20 %)** conditionnent sur
`preferred_moves`, dont **31 des 37 phrases de GESTE_SIGNATURE** (BUT en a
20, CARTON_ROUGE 5). Pour ~95 % des joueurs réels, ces 56 phrases ne
peuvent statistiquement jamais sortir — pas parce qu'elles sont mal
écrites, mais parce que la donnée qui les déclenche n'existe pas pour la
quasi-totalité de la base.

**Deux réponses possibles, ni l'une ni l'autre traitée ici (décision
éditoriale + technique, hors périmètre "plan") :**
- Enrichir `joueurs.xlsx` en `preferred_moves` pour une part significative
  de la base (travail de données, pas d'écriture).
- Donner à `phrase_selector` (une fois implémenté) un vrai fallback à
  l'étape 7 de son algorithme documenté ("0 candidat après filtrage ->
  fallback explicite, à définir") plutôt que de laisser GESTE_SIGNATURE
  silencieusement vide pour 95 % des joueurs.

Je le place en tête de ce plan parce qu'il touche la banque **déjà
livrée**, pas seulement les scénarios à créer — l'ouvrir en V2 sans y
toucher reproduirait le même problème à plus grande échelle sur les
nouveaux scénarios qui utiliseraient `preferred_moves`.

## Méthode de calibrage du volume cible

`volume_cible ≈ fréquence_par_match × 8`, plancher 15 phrases (le plus
petit pool déjà accepté, PENALTY_RATE), majoré quand le scénario recouvre
plusieurs actions distinctes (ex. DÉFENSE = tacle + interception +
dégagement). Le ×8 donne une marge confortable : même sans cooldown, un
scénario à fréquence F ne devrait pas répéter une phrase au sein d'un seul
match. Point de calibrage : l'existant est inconsistant (CARTON_ROUGE est
sur-investi relatif à sa fréquence quasi nulle, CONSTRUCTION est
sous-investi d'un facteur ~10) — je ne réplique pas ce déséquilibre, je
pars de la fréquence réelle à chaque fois.

---

## Scénarios à créer (12) — fiches par ordre de priorité

### Tier 1 — fréquence haute, absence la plus visible à l'écran

#### DÉFENSE
- **Fréquence réelle estimée** : ~30-40/match (tacles réussis + interceptions + dégagements cumulés) — l'action la plus fréquente après CONSTRUCTION.
- **Slots** : `joueur` (défenseur), `adversaire` — réutilise la convention existante, pas de nouveau slot.
- **Conditions types** : `Tackling >= 80` (tacle propre) ; `Pace >= 85 et minute >= 80` (interception décisive tardive) ; `height_cm >= 190` (dégagement aérien dominant).
- **Volume cible** : **50** (couvre 3 sous-actions distinctes — tacle, interception, dégagement — chacune avec sa propre variété).
- **Cooldown proposé** : 2 (même tier de fréquence qu'ARRET_GARDIEN/CONSTRUCTION).
- **Priorité** : Tier 1.

#### CORNER
- **Fréquence réelle estimée** : ~10-12/match.
- **Slots** : `passeur`, `receveur`, `adversaire` (même patron que COUP_FRANC — un tireur, un réceptionneur).
- **Conditions types** : `Heading >= 80 et height_cm >= 185` (tête à la réception) ; `Strength >= 80` (jeu aérien physique) ; `Technique >= 85` (corner joué court, combinaison).
- **Volume cible** : **40** (calibré sur COUP_FRANC, fréquence comparable, mêmes sous-styles : direct au premier poteau, second poteau, jeu court).
- **Cooldown proposé** : 3 (même tier que BUT/COUP_FRANC).
- **Priorité** : Tier 1.

#### FAUTE_SIMPLE
- **Fréquence réelle estimée** : ~20-25/match (fautes non sanctionnées d'un carton).
- **Slots** : `joueur`, `adversaire`, `minute`.
- **Conditions types** : `Aggression >= 60` (faute tactique, sous le seuil des cartons) ; `Tackling <= 50` (maladresse plutôt que dureté) ; `minute >= 80` (faute pour casser un rythme en fin de match).
- **Volume cible** : **35**.
- **Cooldown proposé** : 2 (fréquence proche de CONSTRUCTION/ARRET_GARDIEN).
- **Priorité** : Tier 1.

#### TIR_NON_CADRÉ
- **Fréquence réelle estimée** : ~10/match (sur ~25 tirs, ~10-12 cadrés, ~2-3 buts, le reste hors cadre/contré — TIR_NON_CADRÉ couvre le "hors cadre").
- **Slots** : `joueur`, `adversaire`, `club`.
- **Conditions types** : `Finishing <= 60` (finition imprécise) ; `preferred_moves contient "Shoots From Distance"` (tentative lointaine qui file au-dessus) — **dépend du même enrichissement `preferred_moves` que le constat transversal ci-dessus, à ne pas sur-utiliser ici**.
- **Volume cible** : **30**.
- **Cooldown proposé** : 3 (même tier que BUT, dont c'est le miroir "raté").
- **Priorité** : Tier 1.

#### CARTON_JAUNE
- **Fréquence réelle estimée** : ~3-4/match — bien plus fréquent que CARTON_ROUGE, moins choquant.
- **Slots** : `joueur`, `adversaire`, `club`, `minute` (identique à CARTON_ROUGE).
- **Conditions types** : `Aggression >= 60` (seuil sous celui de CARTON_ROUGE, 75-90) ; `preferred_moves contient "Argues With Officials"` ; `minute <= 30` (carton précoce, risque de deuxième jaune à gérer plus tard dans le match — narrative à garder en tête pour une V3 anti-répétition, pas ce tour).
- **Volume cible** : **30** (plus fréquent que CARTON_ROUGE, mérite un pool comparable pour ne pas se répéter 3-4 fois par match).
- **Cooldown proposé** : 3 (entre CARTON_ROUGE et BUT — fréquent mais pas anodin).
- **Priorité** : Tier 1.

#### REMPLACEMENT
- **Fréquence réelle estimée** : ~5-8/match (jusqu'à 5 par équipe selon compétition).
- **Slots** : **deux joueurs, nouveau patron** — `sortant`, `entrant` (sur le modèle `passeur`/`receveur` de COUP_FRANC/CONSTRUCTION), plus `club`, `minute`.
- **Conditions types** : `age(sortant) >= 32` (sortie liée à la fatigue) ; `minute >= 70` (changement tactique tardif) ; `fm_rating(sortant) <= 60` (performance décevante — nécessite de vérifier que `fm_rating` est bien lisible côté conditions, actuellement un champ Player non listé dans `PLAYER_FIELDS`, voir remarque technique plus bas).
- **Volume cible** : **25**.
- **Cooldown proposé** : 2 (fréquent, peu individuellement marquant sauf sortie sur blessure — voir BLESSURE).
- **Priorité** : Tier 1.
- **Remarque technique pour le tour d'implémentation** : `sortant`/`entrant` sont deux `Player` distincts sur le même événement — même décision de conception que `passeur`/`receveur` sur `MatchContext` (voir `engine/models.py`, commentaire du 30/09/2026 sur `passeur`/`receveur`), pas une nouvelle structure.

### Tier 2 — fréquents mais moins immédiatement remarqués si absents

#### HORS-JEU
- **Fréquence réelle estimée** : ~3-4/match.
- **Slots** : `joueur`, `adversaire`.
- **Conditions types** : `Pace >= 88` (attaquant qui anticipe la ligne) ; `minute >= 80 et score_context == "reduit_ecart"` (prise de risque en fin de match).
- **Volume cible** : **20**.
- **Cooldown proposé** : 3.
- **Priorité** : Tier 2.

#### MI_TEMPS_FIN_MATCH
- **Fréquence réelle estimée** : exactement 2/match (garanti) — deux variantes (`MI_TEMPS`, `FIN_MATCH`), sur le modèle DEFAUT/PENALTY/SURNOM de BUT.
- **Slots** : `club`, `adversaire` — **+ un slot score à concevoir** : ni `home_score` ni `away_score` seuls ne suffisent (il faut les DEUX dans le texte, ex. "2-1"). Proposition : une property `MatchContext.score_display` sur le modèle d'`opponent_team` (déjà une property dérivée, pas un champ stocké), plutôt que d'inventer deux slots séparés à recombiner côté template — décision technique pour le tour d'implémentation, pas tranchée ici.
- **Conditions types** : `score_context == "egalisation"` (mi-temps sur une égalisation qui change la physionomie) ; `minute >= 90` (implicite pour FIN_MATCH, pas une condition de phrase mais un déclencheur côté moteur).
- **Volume cible** : **25** (15 MI_TEMPS + 10 FIN_MATCH, la mi-temps a plus de sous-cas : score serré / domination / retournement).
- **Cooldown proposé** : 4 (même tier que DEBUT_MATCH — contexte factuel qui reste vrai plusieurs semaines).
- **Priorité** : Tier 2.

#### BLESSURE
- **Fréquence réelle estimée** : ~1-2/match en moyenne (loin d'être systématique).
- **Slots** : `joueur`, `club`.
- **Conditions types** : `age >= 30` (blessure liée à l'usure) — la plupart des phrases de ce scénario n'ont probablement PAS besoin de condition (une blessure peut arriver à n'importe qui), à l'inverse des autres scénarios où les conditions dominent.
- **Volume cible** : **20**.
- **Cooldown proposé** : 4 (rare, moment qui casse le rythme du match, mémorable sans être choquant comme un carton rouge).
- **Priorité** : Tier 2.

#### AMBIANCE
- **Fréquence réelle estimée** : ~3-5/match (chants, tifos, incidents de tribune — hors SITUATION_MATCH qui couvre déjà la dynamique tactique).
- **Slots** : `club`, `adversaire`.
- **Conditions types** : `score_context == "creuse_ecart"` (tifo de soutien dans la difficulté) ; pas de condition Player (scénario centré sur le stade, pas un joueur).
- **Volume cible** : **25**.
- **Cooldown proposé** : 2 (fréquent, peu individuellement marquant, comme SITUATION_MATCH).
- **Priorité** : Tier 2.

### Tier 3 — rares ou plus complexes à modéliser proprement

#### STATISTIQUES_PÉRIODIQUES
- **Fréquence réelle estimée** : ~4-6/match (point tactique périodique, ex. toutes les 15-20 minutes).
- **Slots** : `club`, `adversaire` — **+ des champs qui n'existent pas encore sur `MatchContext`** (possession cumulée, tirs cumulés, etc.) : ce scénario a un prérequis structurel (extension de `MatchContext`) plus lourd que les autres, d'où le Tier 3.
- **Conditions types** : `minute >= 45` (bilan de première mi-temps) ; `score_context` divers.
- **Volume cible** : **20**.
- **Cooldown proposé** : 2.
- **Priorité** : Tier 3 — dépend d'abord d'une décision hors-périmètre éditorial (quelles statistiques le moteur de simulation expose-t-il réellement ?).

#### VAR
- **Fréquence réelle estimée** : ~0-1/match en moyenne (toutes les rencontres n'ont pas de review).
- **Slots** : `joueur`, `club`, `adversaire` — **+ un statut de décision** (validé/annulé), à modéliser probablement via `dictionary_key` (slots.yml) plutôt qu'une expression dynamique, puisque c'est un choix narratif fermé (2 issues), pas une valeur calculée.
- **Conditions types** : `score_context` (le but examiné, avant/après review) ; peu de conditions Player pertinentes — le VAR est un événement d'arbitrage, pas une action de joueur.
- **Volume cible** : **20** (10 validé + 10 annulé).
- **Cooldown proposé** : 6 (rare et potentiellement polémique — mémoire longue).
- **Priorité** : Tier 3 — narrative en 2 temps (annonce de la review, puis décision) plus complexe que les scénarios à 1 seul temps existants ; à concevoir avec soin plutôt qu'à la va-vite.

---

## Scénarios sous-alimentés à renforcer (4)

| Scénario | Volume actuel | Volume cible | Delta | Raison |
|---|---|---|---|---|
| CONSTRUCTION | 20 | 60 | **+40** | Fréquence la plus élevée de toute la banque (~15-20 occurrences/match) contre le plus petit pool actuel — le déséquilibre le plus sévère du lot. |
| ARRET_GARDIEN | 38 | 55 | **+17** | Fréquence élevée (~5-8 arrêts/match), pool déjà correct mais cooldown court (2) le rend vite sensible à la casse. |
| SITUATION_MATCH | 30 | 45 | **+15** | Cooldown le plus court du lot (1 match, par design — commentaire quasi continu) : le pool doit être le plus large possible pour ce cooldown, pas le contraire. |
| COUP_FRANC | 20 | 35 | **+15** | Pool le plus petit des scénarios "action" restants ; la redondance structurelle déjà corrigée (35 %→10 %) libère de la place pour de nouvelles amorces plutôt que de nouvelles variantes des mêmes 5 "sur ce coup franc". |

---

## Estimation d'effort total

Unité : **nombre de phrases × complexité des conditions** (pas d'heures
fictives — la complexité conditionne le temps de rédaction bien plus que
le nombre brut).

Trois niveaux de complexité, calibrés sur l'existant :
- **Simple** (0-1 condition, souvent aucune) : DÉBUT_MATCH, SITUATION_MATCH, AMBIANCE, BLESSURE, MI_TEMPS_FIN_MATCH, STATISTIQUES_PÉRIODIQUES.
- **Moyenne** (1-2 conditions, un seul attribut à vérifier) : CONSTRUCTION, ARRET_GARDIEN, COUP_FRANC, CORNER, DÉFENSE, FAUTE_SIMPLE, TIR_NON_CADRÉ, HORS-JEU, REMPLACEMENT.
- **Complexe** (2+ conditions croisées, ou narrative à 2 temps) : CARTON_ROUGE (existant, référence), CARTON_JAUNE, GESTE_SIGNATURE (existant, référence), VAR.

| Bloc | Phrases | Complexité dominante | Effort relatif (phrases × poids complexité) |
|---|---|---|---|
| 12 nouveaux scénarios | 340 | Mixte (voir fiches) | ~340 × 1,4 (moyenne pondérée) ≈ **475 unités** |
| 4 renforcements | 87 | Moyenne (aligné sur l'existant du scénario) | 87 × 1,2 ≈ **105 unités** |
| **Total v2** | **427 phrases nouvelles** (281 + 427 ≈ **708** au total) | — | **≈ 580 unités d'effort** |

Poids de complexité utilisés : Simple = ×1, Moyenne = ×1,3, Complexe = ×2
(calibré sur le temps déjà observé pour concevoir les conditions
croisées de GESTE_SIGNATURE/CARTON_ROUGE au tour précédent, sensiblement
plus long par phrase que SITUATION_MATCH/DEBUT_MATCH qui n'en ont
quasiment pas).

**Cible finale : ~708 phrases** — dans la fourchette 700-800 demandée,
sans forcer artificiellement un chiffre rond.

## Ce que ce plan ne tranche pas (hors périmètre "plan éditorial")

- Le fallback `phrase_selector` étape 7 (0 candidat) — décision
  d'architecture, voir constat transversal.
- L'extension de `MatchContext` pour STATISTIQUES_PÉRIODIQUES — décision
  technique liée à ce que le moteur de simulation expose réellement.
- `score_display` pour MI_TEMPS_FIN_MATCH — décision technique mineure
  mais réelle.
- L'enrichissement de `joueurs.xlsx` en `preferred_moves` — travail de
  données, pas d'écriture éditoriale.

Aucune de ces décisions n'a été prise dans ce tour ; le prochain tour
d'exécution (ouverture des scénarios Tier 1) devra les trancher avant
d'écrire la moindre phrase conditionnée sur ces éléments.
