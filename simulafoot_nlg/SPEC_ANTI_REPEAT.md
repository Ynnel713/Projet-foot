# Spec anti_repeat.py — dette bloquante documentée (audit du 2026-09-30)

`engine/anti_repeat.py` est un squelette (`NotImplementedError` sur les 3
fonctions publiques). Ce document n'implémente rien — c'est le cahier des
charges du prochain tour, tel que demandé par l'audit éditorial de la
banque de 281 phrases. Zéro ligne ajoutée à `engine/` pendant cet audit.

## Interface attendue (déjà figée dans la docstring du squelette)

```python
def recency_penalty(conn: Connection, phrase: Phrase, player: Player, match_id: str) -> float:
    """[0, 1]. 0 = cooldown largement écoulé. 1 = cooldown pas écoulé."""

def similarity_penalty(conn: Connection, candidate_text: str, player: Player) -> float:
    """[0, 1], croissante avec la similarité au texte le plus proche déjà vu."""

def update_cooldown(conn: Connection, phrase: Phrase, player: Player, match_id: str, rendered_text: str) -> None:
    """Enregistre l'usage après rendu (template_filler + post_process)."""
```

Ces trois signatures ne sont **pas** en cause — elles correspondent au
schéma existant (`phrase_history`, `phrase_cooldowns`,
`similarity_signatures`, voir `data/schema.sql`). Le blocage n'est pas
l'interface, c'est l'état des données qu'elle suppose disponible.

## Trois décisions d'architecture non tranchées (bloquantes, pas des détails)

### 1. "Matchs écoulés" n'existe nulle part dans le schéma
`phrase_history.used_at` est un timestamp (`datetime('now')`), pas un
compteur de matchs. Il n'y a **aucune table `matches`** qui séquence les
`match_id` dans l'ordre chronologique par joueur/compétition — `match_id`
est un simple `TEXT` libre partout (`phrase_history`, `MatchContext`).

`recency_penalty` ne peut donc pas répondre à "combien de matchs se sont
écoulés depuis le dernier usage" sans qu'une des deux décisions suivantes
soit prise :
- **(a)** ajouter une table `matches(id, played_at, journee, ...)` et
  joindre `phrase_history.match_id` dessus pour dériver un rang ;
- **(b)** faire porter ce calcul à l'appelant (le moteur de simulation, qui
  connaît déjà l'ordre des matchs) et lui faire passer un compteur explicite
  (`matches_since: int`) en plus de `match_id`, au prix d'un changement de
  signature de `recency_penalty`.

C'est exactement le doute que le squelette documentait déjà ("a definir :
soit un compteur de matchs explicite... soit derive de match_id via une
table de matchs a venir") — cet audit confirme qu'aucune des deux n'a
depuis été tranchée, ni dans le schéma ni dans le code.

### 2. Source du cooldown — RÉSOLU pour les 281 phrases v1 (corrigé le 01/10/2026)
**État actuel (vérifié dans le code et la base) :** chaque phrase de `scenarios.yml` porte un
`cooldown_matches`, attribué à la conversion depuis `DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO`
(`scripts/convert_commentary_xlsx_to_yaml.py:136` ; la conversion échoue si le scénario n'y
figure pas). `scripts/import_seed.py` refuse toute phrase sans `cooldown_matches` (l. 85-90) et
insère dans `phrase_cooldowns` (l. 149). En base : **281/281** lignes peuplées (valeurs 1 à 10 :
SITUATION_MATCH 1 ; ARRET_GARDIEN, CONSTRUCTION 2 ; BUT, COUP_FRANC 3 ; DEBUT_MATCH 4 ;
GESTE_SIGNATURE 5 ; PENALTY_RATE 6 ; CARTON_ROUGE 10).

*Historique (audit du 30/09/2026, antérieur à l'import `ac3bd30`, devenu inexact) : le YAML
n'avait alors aucun champ cooldown et l'import ne peuplait pas `phrase_cooldowns`, d'où la
question (a) champ par phrase / (b) valeur par défaut.* Elle est tranchée en pratique : la
valeur est définie PAR SCÉNARIO (dictionnaire), stockée PAR PHRASE (table), évaluée par
(phrase, joueur) (`phrase_history`).

**Reste à faire pour V2 (décision A2 RÉVISÉE du 01/10/2026, sous-tâche du bloc 1) :** construire
le chemin `pilotes_v2/` → YAML → `import_seed.py` (voir la note A2 révisée, §6). Y entrent les
8 nouveaux scénarios au dictionnaire des cooldowns — 2 : DEFENSE, REMPLACEMENT, FAUTE_SIMPLE,
AMBIANCE ; 3 : CORNER, TIR_NON_CADRE, CARTON_JAUNE, HORS_JEU. Les pilotes sont des modules Python
(`pilotes_v2/*.py`), non des lignes du classeur : ce chemin n'existe pas encore.

### 3. `similarity_penalty` a besoin d'un texte qui n'existe pas encore
Le schéma est clair : `similarity_signatures.signature` correspond au texte
de `phrase_history.rendered_text`, c'est-à-dire le texte **après**
`template_filler.render` et `post_process.apply` — deux squelettes
également non implémentés. Calculer une signature MinHash/k-shingles sur
les *gabarits bruts* (avant substitution des `{slot_name}`) serait un proxy
différent de ce que le schéma documente : deux gabarits identiques rendus
pour deux joueurs différents produisent des textes différents (noms
distincts) mais la même signature de gabarit, ce qui sous-estimerait la
diversité perçue par un spectateur. À l'inverse, ignorer ce proxy revient à
attendre l'implémentation de `template_filler`/`post_process` avant de
pouvoir tester quoi que ce soit ici.

### 4. `similarity_penalty` doit couvrir la répétition THÉMATIQUE, pas seulement lexicale (ajouté le 01/10/2026)

Trouvé en auditant la séquence du pilote DÉFENSE (32 phrases aujourd'hui ; 28 à l'époque de
l'audit, avant l'ajout des 4 phrases de repli α, voir
`data/seed/PLAN_V2_EDITORIAL.md`) : sur un tirage aléatoire donné, 3
phrases à thème "duel aérien"/tête se sont retrouvées consécutives alors
qu'aucune ne partageait le moindre n-gramme de texte avec une autre (zéro
collision lexicale, vérifié mécaniquement). Un `similarity_penalty` basé
sur une signature MinHash/k-shingles du texte rendu (voir point 3
ci-dessus) ne détecterait PAS ce cas : les textes sont lexicalement
distincts, seul le THÈME narratif (ici : "contact aérien") se répète.

Implication pour l'implémentation future : `similarity_penalty` (ou un
mécanisme complémentaire à spécifier) devra pouvoir comparer les
candidats sur un axe thématique/tag (ex. un tag "aérien" porté par la
Phrase ou dérivé de ses conditions `Heading`/`height_cm`), pas uniquement
sur la similarité textuelle du rendu. Piste à creuser à l'implémentation
réelle, pas tranchée ici : soit un tag explicite par phrase (colonne
`tags`/`phrase_tags`, déjà présente dans le schéma mais actuellement
libre et non structurée), soit une heuristique dérivée des attributs
conditionnants communs entre phrases d'un même scénario.

### 5. Dettes éditoriales REMPLACEMENT (ajouté le 01/10/2026, décisions de l'architecte)

Pas des blocages d'`anti_repeat`, mais des limites à ne pas perdre de vue
quand le sélecteur sera implémenté (`pilotes_v2/remplacement.py` en reprend
l'essentiel en docstring) :

- **`score_context` non utilisé dans REMPLACEMENT** (décision du
  01/10/2026). Raison : le sélecteur n'existe pas encore, on ne sait pas si
  `score_context` sera fiable à l'usage, et ses valeurs actuelles
  (`SCORE_CONTEXT_VALUES`) décrivent un BUT, pas un remplacement. Les 21
  phrases sont neutres vis-à-vis du score. À rouvrir en v2.1 SI un besoin
  réel émerge (nouvelles valeurs menant / mené / égalité, à calibrer).
- **Option C ACTÉE comme architecture cible (01/10/2026)** : le sélecteur
  choisira la variante selon le profil du remplacement (il connaît entrant
  ET sortant), pas la grammaire de conditions (plate, un seul `Player` par
  condition). Le pilote reste écrit sous l'option A (conditions sur
  l'entrant). **Dette V2.1 :** C suppose un sélecteur profil-aware ; les 21
  phrases actuelles sont compatibles mais non optimales ; V2.1 scindera les
  pools en sous-variantes (défensif / offensif) si nécessaire, quand le
  sélecteur existera.
- **Surnoms vétéran / joker** : incluent des gardiens (la position n'est pas
  conditionnable). Limitation acceptée et documentée, pas un bug.
- **Surnoms partagés entre scénarios** : « sage » (`age >= 34`) existe dans
  ARRET_GARDIEN (gardiens) et CARTON_JAUNE (tous postes) avec la MÊME
  condition, volontairement : un joueur garde le même surnom d'un scénario à
  l'autre. Risque d'usage : un même joueur « sage » dans deux pools peut se
  sentir répétitif ; à mesurer à l'usage, dette V2.1. Même logique pour
  éclair (`Pace >= 90`), artiste (`Technique >= 90`), pépite (`age <= 18`).
- **« provocateur » (CARTON_JAUNE) : 29 joueurs** (`preferred_moves contient
  "Winds Up Opponents"`) — fantôme borderline accepté (seuil 20), registre
  éditorialement utile ; dépend de l'enrichissement `preferred_moves`.
- **Répétition thématique (H3) CARTON_JAUNE** : « tacle » (5 phrases) et
  « sanction » (6) acceptés comme CORNER (« la tête », fin « {adversaire} »),
  sans collision lexicale ; `similarity_penalty` sur texte rendu ne les
  détecterait pas (voir décision 4).
- **MI_TEMPS_FIN_MATCH : option C (01/10/2026)** — le sélecteur choisit
  mi-temps vs fin de match et la valence du résultat ; les phrases ne
  conditionnent que sur `minute`. `MatchContext.score_display` n'existe pas :
  dette V2.1, les textes avec score chiffré attendent. Même famille que
  REMPLACEMENT (option C).
- **Conditions booléennes / valeurs inconnues** : `is_home` lisible depuis le
  01/10/2026 (`MATCH_CONTEXT_FIELDS`), avec cast `true/vrai/false/faux` et
  « valeur inconnue ⇒ aucune condition ne matche ».
- **Position exposée aux conditions (option A, 01/10/2026)** : couverture
  7563/7563 = 100 % (seuil de décision : 90 %). `position` dans `PLAYER_FIELDS`.
  Option D (fusion Off the Ball / off côté) reste notée comme fallback si
  Position devait être retirée ; non retenue.
- **Double jaune : V3 (01/10/2026) — « mesure non faite ; ordre de grandeur
  football ~1 double jaune sur 15-20 matchs ; à instrumenter quand le moteur sera
  capable de générer un second jaune sur le même joueur ».** Détail : Aucune phrase CARTON_JAUNE ne suggère un
  premier ou second avertissement ; la gestion d'un deuxième jaune dans le même
  match (et le rouge qui s'ensuit) est reportée à V3. **Aucun chiffre de fréquence
  n'est retenu dans ce dépôt** : le « 1 match, 9 joueurs » évoqué en revue ne
  figure dans aucun fichier ni calcul (le seul « 1 match » du dépôt est le cooldown
  de SITUATION_MATCH). L'ordre de grandeur football cité par l'architecte
  (~1 double jaune par joueur sur 15-20 matchs) est fourni, non mesuré ici ; à
  mesurer sur les matchs simulés avant de dimensionner la V3.
- **AMBIANCE sans SURNOM (01/10/2026)** : le scénario n'a pas de joueur ;
  « gros derby » et « petite équipe qui reçoit le leader » exigent de la donnée
  absente du moteur (rivalité entre clubs, classement). `competition` et
  `journee` existent sur `MatchContext` mais ne sont pas dans
  `MATCH_CONTEXT_FIELDS`. Reprendre si ces données arrivent (soit exposer
  `competition`/`journee`, soit ajouter une table de rivalités/classement).
- **Vérification de l'outil `audit_conditions_pilote` et règle universelle de
  domination (01/10/2026).** Le soupçon de bug (max au lieu d'intersection) était un
  faux positif de lecture : l'outil calcule l'intersection réelle
  (`tests/test_audit_conditions_pilote.py`). La domination se juge sur la
  DISTRIBUTION, pas sur le compte de phrases > 50 % : **alerte à 3 phrases dont la
  sélectivité dépasse 70 %** (tolérance : 2), règle codée dans l'outil
  (`SEUIL_TRES_DOMINANTE`, `MAX_TRES_DOMINANTES`) et vérifiée par un test sur
  chaque pilote. Mesure par tranche de 10 % (joueurs de champ) :

  | Pilote | < 40 % | 40-50 | 50-60 | 60-70 | 70-80 | ≥ 80 | sans condition |
  |---|---|---|---|---|---|---|---|
  | FAUTE_SIMPLE | 9 | 4 | 6 | 4 | **2** | 0 | 1 |
  | DÉFENSE | 27 | 0 | 0 | 0 | 0 | 0 | 1 |
  | CORNER | 22 | 0 | 0 | 0 | 0 | 0 | 4 |
  | TIR_NON_CADRÉ | 20 | 0 | 0 | 0 | 0 | 0 | 8 |
  | REMPLACEMENT | 12 | 0 | 0 | 0 | 0 | 0 | 9 |
  | CARTON_JAUNE | 18 | 0 | 0 | 0 | 0 | 0 | 10 |

  FAUTE_SIMPLE : 12 phrases à 50-76 %, aucune à 80 %+, 2 à 70-80 % (#15 à 75,6 %,
  #16 à 74,8 % dont la `minute` est ignorée par l'outil, donc sur-estimée) —
  ni homogène ni polarisé, **sous le seuil d'alerte, ne rouvre pas** le pilote.
  Les phrases SANS condition (colonne de droite) sont toujours éligibles : à
  suivre au moment du sélecteur (CARTON_JAUNE 10/28, REMPLACEMENT 9/21).
- **Chevauchement de surnoms, deux cas distincts, tous deux AUTORISÉS (décision B3 précisée,
  01/10/2026) :** (1) *un même joueur déclenche le même surnom dans deux scénarios* (ex.
  « renard », `Finishing >= 85`, sur TIR_NON_CADRÉ et sur HORS-JEU dans le même match) — voulu :
  même archétype d'un scénario à l'autre ; (2) *deux joueurs d'un même match partagent un même
  surnom* — cas rare, non mesuré, dette documentée ; à rouvrir si un match réel produit une
  confusion.
- **« Retour de blessure »** : aucune donnée (`players.status` n'a pas de
  valeur blessé/retour) — aucune phrase possible. À rouvrir avec BLESSURE
  (Tier 2) si la donnée arrive.

### 6. Sélecteur : α (spécifique d'abord) — décision révisée du 01/10/2026, pour V2.1

**Décision (architecte) : α reste la cible, avec DEUX prérequis obligatoires.** Parmi
les candidates d'une variante, une phrase dont une condition joueur matche PRIME sur
les phrases sans condition ; les sans-condition servent de repli. Option β (tirage
uniforme) écartée : elle diluerait le travail de catégorisation. Aucune implémentation
(le sélecteur n'existe pas). Argumenter AVANT pour revenir sur α.

**Mesure initiale (joueurs de champ, DEFAUT) qui a motivé les prérequis :**
DÉFENSE 74,2 % et CORNER 71,8 % des joueurs n'avaient AUCUNE phrase spécifique ; pool
spécifique moyen 0,5 et 1,0. Ce n'est pas une question de politique de sélection (α ou
β donnent la même unique phrase à ces joueurs) mais de DIMENSIONNEMENT du pool.

**Prérequis 1 — pool dimensionné (fait le 01/10/2026 pour DÉFENSE et CORNER).**
Réécriture ciblée, 4 phrases neutres (sans condition) ajoutées à chacun, plutôt
qu'un élargissement des conditions (qui dévaluerait la catégorisation) :
DÉFENSE 1 → 5 sans-condition (22 → 26 DEFAUT), CORNER 4 → 8 (20 → 24 DEFAUT).
Précision de lecture : ces ajouts ne changent PAS le nombre moyen de phrases
*spécifiques* par joueur (0,5 et 1,0) ; ils dimensionnent le *pool disponible*
(spécifiques + repli). Le seuil est donc appliqué au pool disponible :

| Pilote | DEFAUT | sans cond. (+ctx) | joueurs à 0 phrase spécifique | pool moyen/joueur | pool minimal |
|---|---|---|---|---|---|
| FAUTE_SIMPLE | 20 | 1 | 7,3 % | 10,3 | 1 |
| DÉFENSE | 26 | 5 | 74,2 % | 5,5 | 5 |
| CORNER | 24 | 8 | 71,8 % | 9,0 | 8 |
| TIR_NON_CADRÉ | 22 | 8 | 28,1 % | 10,0 | 8 |
| REMPLACEMENT | 16 | 9 | 42,0 % | 9,9 | 9 |
| CARTON_JAUNE | 22 | 10 | 42,4 % | 11,8 | 10 |
| HORS-JEU | 19 | 10 | 22,0 % | 11,5 | 10 |
| AMBIANCE | 24 | 24 | 100 % (aucune cond. joueur) | 24,0 | 24 |

Gardé par un test permanent (`test_prerequis_alpha_pool_par_joueur_dimensionne`, sur
tous les pilotes découverts) : pool moyen ≥ 2,5 ET moins de 10 % des joueurs avec un
pool < 3 ; il échoue sur DÉFENSE avant le correctif. Lecture stricte du seuil
« ≥ 2,5 phrases *spécifiques* par joueur » : DÉFENSE (0,5) et CORNER (1,0) restent
dessous ; atteindre ce seuil exigerait d'élargir les conditions (option écartée).

**Prérequis 2 — repli cooldown (déjà noté).** Quand les conditions matchent mais que
les cooldowns sont épuisés, on retombe sur le repli sans condition au lieu de bloquer.

**Dimensionnement à utiliser (correction de la formule précédente).** Le cooldown se
calcule PAR JOUEUR (`phrase_history.player_id`, voir `data/schema.sql`) : le besoin est
« événements du scénario par joueur et par match × cooldown (en matchs) », pas
« événements par match × cooldown » (formule globale utilisée à tort pour le plan
Tier 2, qui surestime). **Risque résiduel DÉFENSE (estimation, non mesurée)** : ~30-40
événements/match concentrés sur ~8 joueurs actifs ⇒ ~4 par joueur et par match ×
cooldown 2 ⇒ ~8-9 phrases disponibles nécessaires pour les plus sollicités, contre un
pool minimal de 5. À confirmer sur des matchs simulés avant d'ajouter 3-4 neutres.

**Points à trancher en V2.1 (non décidés ici) :**
- la docstring de `phrase_selector.select` (étape 6) décrit un tirage pondéré parmi
  TOUTES les candidates d'une variante, soit β ; α exige un palier de priorité ;
- ~~le SURNOM est une variante séparée que la cascade (étape 7) n'essaie qu'APRÈS un
  DEFAUT à 0 candidat~~ **tranché par D1 (note ci-dessous).**
- granularité de « spécifique » : **tranché à 70 %** (décision B2 du 01/10/2026) — une
  phrase à condition large (ex. `Aggression >= 45`, 80 %) n'est PAS spécifique.

**Note D1 — ordre réel de la cascade : SURNOM → DEFAUT (décision du 01/10/2026).** Les phrases
SURNOM (surnom vétéran, joker, etc., conditionnées) sont essayées EN PREMIER : si l'une matche
(et que son cooldown est écoulé), elle prime ; sinon on retombe sur DEFAUT, avec le repli
cooldown entre les deux (prérequis 2). C'est α appliqué aux surnoms. Raison : un ordre
« DEFAUT d'abord, SURNOM si DEFAUT n'a aucun candidat » rendrait les 48 phrases SURNOM
mortes, car avec 5-10 phrases sans condition en repli, DEFAUT n'a jamais 0 candidat. Les
SURNOM ne sont donc jamais « cascade de repli » : c'est le palier prioritaire. La docstring
de `phrase_selector.select` (étapes 2, 6 et 7) devra suivre ; elle décrit aujourd'hui, à
l'étape 7.a, un essai des variantes non par défaut puis de la variante par défaut en dernier
recours après 0 survivant.

**Note A2 révisée — chemin pilotes → YAML (01/10/2026).** Le dictionnaire des cooldowns n'est
lu que par la conversion classeur → YAML ; les pilotes sont des modules Python. Décision :
construire le chemin `pilotes_v2/` → YAML → `import_seed.py`, même forme que le pipeline v1
(classeur → YAML → base) ; pas d'import direct de modules Python en base (une seconde source
de vérité). Codes de scénario sans accent ni tiret, en MAJUSCULES avec `_` (DEFENSE,
TIR_NON_CADRE, HORS_JEU, CARTON_JAUNE…), cohérents avec CARTON_ROUGE, ARRET_GARDIEN. Sous-tâche
du bloc 1 (import), non une action isolée.
### 7. Bilan V2 et décision Tier 3 (01/10/2026)

Phrases RÉDIGÉES en pilotes (hors banque : `scenarios.yml` et la base ne contiennent
toujours que les 281 phrases v1, rien n'est importé) :

| Bloc | Phrases |
|---|---|
| Tier 1 (6 pilotes) | DÉFENSE 32, FAUTE_SIMPLE 26, CORNER 30, TIR_NON_CADRÉ 28, REMPLACEMENT 21, CARTON_JAUNE 28 = **165** |
| Tier 2 (2 sur 4) | AMBIANCE 24, HORS-JEU 24 = **48** |
| **Écrit à ce jour** | **213** |

**Tier 3 : décision recommandée.** STATISTIQUES_PÉRIODIQUES est bloqué comme BLESSURE et
MI_TEMPS_FIN_MATCH : il exige des champs absents de `MatchContext` (possession, tirs
cumulés) — aucune phrase chiffrée ne peut s'écrire sans la donnée. VAR est rédigeable :
deux issues (validé / annulé) gérées par le sélecteur (option C), phrases autonomes ;
dépendance résiduelle = le moteur doit émettre un événement VAR. **Ouvrir VAR seul
(20 phrases : 10 validé + 10 annulé, cooldown 6), laisser STATISTIQUES_PÉRIODIQUES en
dette données.** VAR, finalement DIFFÉRÉ (le moteur n'émet pas d'événement VAR, décision du 01/10/2026),
n'est pas écrit : **total rédigé = 213** phrases.

Ce que ce total ne contient PAS (à acter explicitement) :
- **3 scénarios bloqués** : BLESSURE (20), MI_TEMPS_FIN_MATCH (25), STATISTIQUES_PÉRIODIQUES (20)
  = 65 phrases du plan en dette (données status / `score_display` / stats `MatchContext`) ;
- **écart aux volumes cibles du plan** : 12 scénarios ciblés à 340 phrases ; pilotes
  Tier 1 à 165 pour 210 visées (DÉFENSE 32/50, CORNER 30/40, FAUTE_SIMPLE 26/35,
  TIR_NON_CADRÉ 28/30, CARTON_JAUNE 28/30, REMPLACEMENT 21/25) ;
- **les 4 renforcements du plan (87 phrases) ne sont dans aucun Tier** : CONSTRUCTION
  20 → 60 (+40, fréquence 15-20/match pour le plus petit pool : « déséquilibre le plus
  sévère » selon le plan), ARRET_GARDIEN +17, SITUATION_MATCH +15, COUP_FRANC +15. Ce
  chantier n'est ni ouvert ni refermé : à décider.
Le 708 du plan v2 (281 + 427) était théorique ; la trajectoire réelle est 281 + 213 =
**494 phrases** (+ 87 si les renforcements sont ouverts), soit ~73 % des 340 phrases
visées pour les 12 scénarios.

### 8. Mesures à faire lors de l'implémentation du sélecteur (V2.1)

À ne PAS corriger par anticipation : on mesure d'abord (décision du 01/10/2026).

- **Cooldown et schéma : aucune migration.** `data/schema.sql` suit déjà le cooldown par
  joueur : `phrase_history(phrase_id, player_id, match_id, …)` donne le dernier usage
  d'une phrase PAR JOUEUR, `phrase_cooldowns(phrase_id → cooldown_matches)` porte la
  DURÉE (propriété de la phrase). La « correction » du 01/10/2026 concernait la formule de
  DIMENSIONNEMENT des pools, pas le stockage. `phrase_cooldowns` est peuplée à 281/281 pour la
  v1 (voir §2) ; restent ouverts : la séquence de matchs (« matchs écoulés », décision 1 →
  décision C1 ci-dessous) et les cooldowns des 8 scénarios V2 (décision A2, §2).
- **DÉFENSE — risque résiduel accepté, à mesurer.** Estimation (non mesurée) : ~4 événements
  par joueur et par match pour les plus sollicités, cooldown 2, pool minimal 5 phrases
  (5 sans-condition). Pool suffisant pour un match, tendu sur un cycle de cooldown complet.
  **Protocole :** 10 matchs simulés ; *répétition exacte* = même `phrase_id` rendue deux fois
  pour le même joueur dans un même match. **Seuil : > 5 % ⇒ rouvrir DÉFENSE et ajouter 3-4
  phrases neutres.** Pas avant.
- **Part servie par le repli (α).** Mesurer, par scénario, la part des événements servis par
  une phrase sans condition et la comparer au tableau de la section 6 (ex. DÉFENSE ~74 %
  des joueurs sans phrase spécifique, CORNER ~72 %) ; un écart fort signale des conditions
  trop larges ou une donnée joueur manquante.
- **Part des événements où un SURNOM sort chez un joueur de 35 ans et plus** (conséquence de D1,
  SURNOM prime) : borne haute à vérifier après implémentation (D6, 01/10/2026). Mesure seule :
  ni test ni code.
- **Cooldown épuisé.** Taux d'événements à 0 candidat (cascade, étape 7) par scénario ; doit
  rester rarissime.
- **FAUTE_SIMPLE et CORNER** (20-25 et 10-12 événements par match) : même taux de
  répétition exacte par joueur que DÉFENSE.

### 9. Décisions de cartographie V2.1 (01/10/2026, architecte)

- **A2 (révisée) — chemin pilotes → YAML → `import_seed.py` à construire**, codes sans accent ni
  tiret ; cooldowns V2 par dictionnaire (voir §2 et la note A2 révisée, §6) ; sous-tâche du bloc 1.
- **B1 — α actée ; cascade : voir D1 (SURNOM → DEFAUT).** La docstring de `phrase_selector.select`
  est alignée sur α pour l'étape 6 (commit `48e6bea`) ; son étape 7 reste à réviser selon D1 ;
  aucun code.
- **B2 — « spécifique » = sélectivité ≤ 70 %** (même critère que la domination, §6) : en
  dessous de ce seuil seulement, α apporte quelque chose.
- **B3 (précisée) — deux cas de chevauchement de surnoms, tous deux autorisés** (même joueur
  dans deux scénarios ; deux joueurs d'un même match) : notes distinctes au §5.
- **C1 — ordre des matchs : compteur explicite fourni par l'appelant (précisé).** Champ
  `match_sequence: int` ajouté à `phrase_history` (`ALTER TABLE … ADD COLUMN` avec valeur par
  défaut, même sur table vide, pas de table `matches`) ; paramètre `match_sequence` fourni par
  l'appelant (`recency_penalty` / `update_cooldown`) ; écriture dans `logger.log_usage` ;
  `match_id` reste la clé de jointure. À intégrer au bloc 4 (`anti_repeat`) ; pas ce tour.
- **D1 — cascade SURNOM → DEFAUT** (SURNOM prime quand sa condition matche) : note D1, §6.
- **D3 — `{sortant}` / `{entrant}` : étendre `MatchContext`** avec `sortant: Player | None = None`
  et `entrant: Player | None = None` (deux champs typés, comme `passeur` / `receveur`, pas de
  dict générique). **Impact, 4 endroits (liste corrigée le 01/10/2026 : `profile_engine` manquait) :**
  (1) `engine/models.py` : 2 champs + la note « Autre protagoniste d'un événement à deux
  joueurs » à étendre à REMPLACEMENT ; (2) `engine/profile_engine.normalize_match_context` :
  lecture des 2 clés (il construit `MatchContext` depuis un dict et ne connaît ni `sortant` ni
  `entrant`) ; (3) `convert_commentary_xlsx_to_yaml.py` : `SLOT_EXPRESSIONS`
  (`context.sortant.full_name`, `context.entrant.full_name`) et `SLOTS_AUTORISES["REMPLACEMENT"]` ;
  (4) `template_filler.render` : gérer les deux slots. Couples à
  deux joueurs existants ou prévus : seulement `passeur`/`receveur` (COUP_FRANC, CONSTRUCTION,
  CORNER) et `sortant`/`entrant` (REMPLACEMENT) — aucune structure générique justifiée.
  **Prérequis du bloc 1 (import), à faire AVANT lui : changement de modèle, pas d'intégration
  runtime ni du bloc 5.**
- **D4 — YAML des pilotes : second fichier, pas de fusion avec v1.** `import_seed.py` accepte une
  LISTE de chemins YAML au lieu d'un seul (`scenarios_path`, `scripts/import_seed.py:186-192`,
  constante `DEFAULT_SCENARIOS_PATH` l. 30). Les 281 phrases v1 ne sont jamais réécrites ; chaque
  pilote peut être un commit séparé ; convention « YAML = source d'import » préservée.
- **D5 — test à renommer :** `test_cascade_activation_is_logged_as_warning`
  (`tests/test_phrase_selector.py`, `TestCascadeDeVariantesSpec`) ne décrit plus la règle (WARNING
  seulement si la variante par défaut rend 0 candidat). Renommage proposé :
  `test_cascade_warning_only_when_default_empty`, dans le même commit que le prochain changement
  touchant `phrase_selector`, jamais en commit isolé.
- **D6 — vétérans :** voir la mesure ajoutée au §8.
- **D7 — import de seed : rebuild des tables de SEED uniquement, joueurs préservés (01/10/2026).**
  Pipeline V2.1 : (1) supprimer les tables de seed — `scenarios`, `variants`, `phrases`,
  `phrase_conditions`, `phrase_slots`, `slot_dictionaries`, `phrase_cooldowns`, `tags`,
  `phrase_tags` ; (2) supprimer le runtime associé — `phrase_history`, `similarity_signatures`
  (cascade depuis `scenarios`, ou suppression explicite, au choix de l'implémentation) ;
  (3) réimporter v1 + V2 en un seul appel avec la liste de chemins (D4). **Ne pas toucher à
  `players` ni `player_attributes`** (refaire `import-players` à chaque import de seed est un
  coût inutile). Pas de changement du `ON DELETE CASCADE` de `phrase_history.phrase_id` : un
  `phrase_id` orphelin est pire qu'une suppression nette.
  **Dette documentée :** perte de `phrase_history` à chaque réimport de seed ; acceptable
  aujourd'hui (zéro match réel en base), à reconsidérer quand le runtime portera des données de
  match réelles.
- **D7bis — `DELETE FROM`, pas `DROP TABLE` (01/10/2026).** Le reset du seed supprime les LIGNES
  dans l'ordre inverse des dépendances, puis `DELETE FROM sqlite_sequence WHERE name IN (…)` pour
  remettre à zéro les compteurs `AUTOINCREMENT` (déterminisme des `phrase_id` à ordre d'insertion
  constant). Compatible clés étrangères ; `schema.sql` reste la seule source du schéma et n'est pas
  ré-exécuté. **Le script de reset seed-scoped est à CRÉER, dans le bloc 1** (aucun script
  d'administration n'existe : `init_db` ne supprime rien). Tables `AUTOINCREMENT` du schéma :
  `player_attributes`, `scenarios`, `variants`, `phrases`, `phrase_conditions`, `phrase_slots`,
  `slot_dictionaries`, `phrase_history`, `similarity_signatures`, `tags` — `player_attributes` n'est
  PAS du seed et ne doit jamais figurer dans la liste du `DELETE FROM sqlite_sequence`.
- **D8 révisée — `phrase_history` conservée dans l'export, note README sur les IDs morts après
  réimport (01/10/2026).** La décision initiale (exclure `phrase_history`) est RETIRÉE : la
  docstring de `export_analytics` vise « quelles phrases sont le plus utilisées par scénario »,
  ce qui exige `phrase_history`. `EXPORTED_TABLES` (`scripts/export_analytics.py:16-22`) reste :
  `scenarios`, `variants`, `phrases`, `phrase_history`, `phrase_cooldowns`. **À faire (README) :**
  les `phrase_id` exportés ne désignent plus rien après un réimport de seed (D7/D7bis) ;
  exporter AVANT un réimport, pas après.
- **Note C1 (bloc 4), corrigée :** `match_sequence` suit DEUX voies qui coexistent :
  `schema.sql` (`CREATE`) pour les bases créées APRÈS le changement, et `ALTER TABLE … ADD COLUMN`
  (avec valeur par défaut) pour TOUTE base existante. `DELETE FROM` (D7bis) ne recrée pas les
  tables : un `CREATE` modifié n'atteint jamais une base déjà créée.
- **Note C2 (bloc 1) :** ajouter un test de non-régression « pas de doublon de code de scénario
  entre v1 et V2 » avec une erreur EXPLICITE (aujourd'hui : `IntegrityError` muette sur la
  contrainte `UNIQUE` de `scenarios.code`).
- **README, ligne 24, à actualiser** : « Charge `data/seed/*.yml` dans SQLite… » →
  « `data/seed/` + `data/seed/v2/` » (D4).
- **C2 — répétition thématique (§4) : hors périmètre V2.1.** Dette de conception ; aucun
  chantier de tagging (`tags` / `phrase_tags` restent vides et inutilisées).

### 10. Décisions OUVERTES remontées à l'architecte (non actées, 01/10/2026)

**D9 — sélectivité à l'exécution (étape 6.a de `phrase_selector.select`).** Quatre options :
(a) colonne matérialisée à l'import — fausse dès que la population de joueurs change ;
(b) calcul à la volée à chaque `select` — correct mais coûteux ; (c) cache mémoire au démarrage —
correct et rapide ; (d) approximation « au moins une condition joueur = spécifique » — dévie du
critère B2 (sélectivité ≤ 70 %). Recommandation : **(c)**. *Décision de l'architecte en attente.*
Faits : aucun cache n'existe dans `simulafoot_nlg/` (des `lru_cache` et `st.cache_data` existent
côté simulation et application, `src/ligue1sim/*.py`, `app.py`, `apps/streamlit_preview.py`, sur les
classeurs `joueurs.xlsx` / `entraineurs.xlsx`, pas sur la base NLG) : à créer. Population de
référence actuelle de la mesure : les joueurs de CHAMP (hors GK, `position != "GK"`), tous postes de
champ confondus — ni toute la base, ni une sous-population par scénario ; la définir pour
l'exécution reste ouvert (ex. `Off the Ball >= 75` : 7,3 % des joueurs de champ, 13,2 % des
attaquants).

**D10 — fallback final (étape 7, dernier paragraphe).** Trois options : (a) phrase générique de
secours par scénario, en base ; (b) exception dédiée ; (c) phrase neutre en dur. Recommandation :
**(a) + WARNING obligatoire** (même niveau que l'étape 7.e). *Décision de l'architecte en
attente.* Faits : aucune table ni colonne de phrase de secours n'existe dans `schema.sql` (à créer) ;
le test `test_cascade_exhaustion_falls_through_to_the_final_fallback` fige les expressions
« fallback final explicite » et « toujours a definir » de la docstring : à mettre à jour avec la
décision.

## Ce qui N'est PAS bloquant (déjà en place)
- Le schéma SQL (`phrase_history`, `phrase_cooldowns`,
  `similarity_signatures`) est cohérent avec l'algorithme documenté dans le
  squelette — pas de refonte de schéma nécessaire, seulement les décisions
  1 et 2 ci-dessus.
- `engine/db.py` fournit déjà les connexions SQLite (WAL, FK).
- Les 281 phrases donnent une base de gabarits suffisante pour mesurer la
  diversité structurelle *en amont* (voir Audit 2 du rapport principal) —
  ce n'est pas une mesure d'anti-répétition en usage réel, mais un signal
  de risque : un scénario à faible diversité de gabarits (ex. COUP_FRANC,
  35 % de signatures jumelles) produira mécaniquement plus de collisions
  perçues même avec un `anti_repeat` parfait, simplement parce que le pool
  de départ est plus petit.

## Séquencement proposé pour le prochain tour
1. Trancher les décisions 1 et 2 ci-dessus (architecture, pas code).
2. Implémenter `template_filler.render` + `post_process.apply` (prérequis
   factuel : sans texte rendu réel, `similarity_penalty` n'a rien à
   comparer).
3. Implémenter `phrase_selector.select` (consommateur direct
   d'`anti_repeat`).
4. Implémenter `anti_repeat.*` pour de vrai, avec les tests que
   `tests/test_anti_repeat.py` ne fait aujourd'hui que documenter en creux
   (contrat `NotImplementedError`).
5. Alors seulement : rejouer un match simulé (90 minutes, ~25 tirs, ~12
   corners, ~3 buts) pour mesurer répétitions exactes et structurelles sous
   5 minutes d'écart, comme demandé par l'audit initial — impossible avant
   les étapes 1 à 4.

**Verdict : dette bloquante, spec livrée, aucune implémentation ce tour.**
