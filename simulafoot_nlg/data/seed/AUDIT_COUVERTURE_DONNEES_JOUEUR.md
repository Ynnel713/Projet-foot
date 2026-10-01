# Audit de couverture des données Player — 30/09/2026

Pause décidée sur l'écriture V2 tant que ce document n'est pas tranché
(voir section 3). Script support : `scripts/audit_couverture_donnees.py`
(hors moteur, ne remplace aucun squelette). Sortie brute complète :
`scripts/_audit_couverture_out.txt`.

**Faisabilité (question posée avant de commencer)** : oui, direct sur les
7563 joueurs, pas d'échantillonnage — une poignée d'agrégations SQL sur
une table de cette taille, de l'ordre de la milliseconde chacune.

> **Mise à jour du 01/10/2026 — `height_cm` RÉSOLU, chiffres de ce
> document devenus historiques pour cet attribut.** Les 11,7 % relevés
> ci-dessous venaient d'un bug de nom de colonne (`import_players.py`
> lisait `"Taille (cm)"` au lieu de `"Taille FM (cm)"`). Vérifié avant
> bascule : sur 93+84 joueurs portant une valeur sentinelle connue sur
> `"Taille (cm)"` (152,4 cm/154,9 cm, conversion pieds/pouces ratée),
> 91 et 82 respectivement récupérables via la colonne FM26, sans
> collision. Correctif appliqué, `import-players` relancé — couverture
> réelle désormais **93,4 %**. Les tableaux ci-dessous ne sont PAS
> corrigés rétroactivement (valeur historique du diagnostic initial) —
> voir [COUVERTURE.md](COUVERTURE.md) et
> [PLAN_V2_EDITORIAL.md](PLAN_V2_EDITORIAL.md) pour l'état courant.

---

## 1. Couverture par attribut

Sur les 7563 joueurs importés, pour chaque attribut référencé par au
moins une des 153 conditions réelles :

| Attribut | Couverture | Distribution | Phrases concernées | Verdict |
|---|---|---|---|---|
| `preferred_moves` | **362/7563 = 4,8 %** | top 5 moves : Runs With Ball Often (77), Tries Killer Balls Often (42), Tries To Play Way Out Of Trouble (41), Plays One-Twos (40), Tries Long Range Passes (39) | 56 | **QUASI-VIDE** |
| `height_cm` | **887/7563 = 11,7 %** | min 152, méd. 182, max 203 | 7 | **QUASI-VIDE** |
| `foot` | **2957/7563 = 39,1 %** | D : 2245, G : 712 | 1 | **PARTIEL** |
| `weak_foot` | 7037/7563 = 93,0 % | min 1, méd. 3, max 4 | 1 | VIABLE |
| `age` | 7563/7563 = 100,0 % | min 15, méd. 25, max 43 | 6 | VIABLE |
| `Aggression` | 7037/7563 = 93,0 % | min 10, méd. 60, max 99 | 27 | VIABLE |
| `Strength` | 7037/7563 = 93,0 % | min 5, méd. 60, max 99 | 6 | VIABLE |
| `Pace` | 7037/7563 = 93,0 % | min 10, méd. 65, max 99 | 5 | VIABLE |
| `Technique` | 7037/7563 = 93,0 % | min 5, méd. 60, max 99 | 4 | VIABLE |
| `Dribbling` | 6193/7563 = 81,9 % | min 5, méd. 60, max 95 | 4 | VIABLE |
| `Finishing` | 6193/7563 = 81,9 % | min 5, méd. 45, max 95 | 3 | VIABLE |
| `Heading` | 6193/7563 = 81,9 % | min 5, méd. 50, max 95 | 3 | VIABLE |
| `Vision` | 7037/7563 = 93,0 % | min 5, méd. 55, max 99 | 2 | VIABLE |
| `Tackling` | 6193/7563 = 81,9 % | min 5, méd. 55, max 95 | 1 | VIABLE |
| `minute`, `score_context` | — | — | 17, 10 | Contexte de match, toujours disponible au runtime — hors périmètre de cet audit |

**Réponse directe à ta question de repriorisation** : non, les autres
attributs critiques (`weak_foot`, `age`) ne sont PAS peu peuplés — ils
sont à 93-100 %, dans la même fourchette que les attributs FM26 standards.
Le problème est concentré sur exactement 3 attributs, tous issus de la
même source (voir section 2) : `preferred_moves` (4,8 %), `height_cm`
(11,7 %), `foot` (39,1 %, partiel mais pas critique). Ce n'est pas la
donnée Player en général qui est trouée — c'est un sous-ensemble
identifiable, dont l'origine est comprise (section 2).

### Taux de déclenchement théorique par phrase — la distinction qui compte

109 des 281 phrases ont au moins une condition portant sur un attribut
joueur (hors `minute`/`score_context`). **102 d'entre elles (93,6 %)**
tombent sous 10 % de taux de déclenchement théorique sur les 7563
joueurs — mais ce chiffre mélange deux causes très différentes qu'il ne
faut pas confondre :

- **63 phrases (57,8 % du total évalué) sont limitées par la DONNÉE** :
  elles conditionnent sur `preferred_moves`, `height_cm` ou `foot` — un
  joueur qui aurait le trait qualifiant ne peut même pas être testé,
  faute de valeur renseignée. **C'est le vrai problème.**
- **39 phrases (35,8 %) sont juste sélectives PAR CONCEPTION** sur un
  attribut bien peuplé (`Aggression >= 85`, `Strength >= 88`...) — peu de
  joueurs atteignent un seuil élitiste voulu, mais l'attribut lui-même
  est disponible à 93 % : un joueur qui a vraiment 95 d'Aggression
  déclenchera la phrase sans problème. **Ce n'est pas un problème, c'est
  la sélectivité narrative qui fait qu'un "colosse" ou un carton rouge
  restent rares — comportement voulu.**

Répartition des 63 phrases data-limitées par scénario : **GESTE_SIGNATURE
32/37 (86 %)**, **BUT 23/60 (38 %)**, **CARTON_ROUGE 5/31 (16 %)**,
**ARRET_GARDIEN 3/38 (8 %)**. GESTE_SIGNATURE est de très loin le
scénario le plus exposé — cohérent avec le fait qu'il a été conçu
spécifiquement pour exploiter `preferred_moves` comme signature d'un
joueur (bon choix éditorial, mauvais choix si la donnée sous-jacente est
absente pour 95 % de la base).

Vérification supplémentaire : sur les 31 moves distincts requis par
GESTE_SIGNATURE, **0 ont zéro joueur correspondant** dans les 7563 — aucune
phrase n'est littéralement morte, chacune matche au moins un des 362
joueurs "riches". Le pool de 30 phrases DEFAUT n'est donc pas surdimensionné
par rapport à sa population adressable (362 joueurs) — il est à peu près
calibré pour elle. Le vrai souci n'est pas un excès de phrases, c'est
l'étroitesse de la population qu'elles peuvent atteindre.

Liste complète des 63 phrases limitées par la donnée (triée par taux
croissant) : voir `scripts/_audit_couverture_out.txt`, section "Limitees
par la donnee". Les 10 plus extrêmes (0,00 %-0,08 %) concernent des moves
FM très spécifiques (ex. "Hits Free Kicks With Power", "Attempts Overhead
Kicks") ou des combinaisons `height_cm` déjà signalées lors de l'audit
éditorial précédent (BUT/SURNOM "Le colosse", ARRET_GARDIEN/SURNOM "Le
mur").

---

## 2. Investigation `add_preferred_moves.py` (lecture seule, non exécuté)

**Ce que le fichier fait réellement (son nom est trompeur)** : il
**n'enrichit aucune donnée joueur**. C'est un script d'auteur qui ajoute
des lignes de PHRASES au classeur de commentaire — concrètement, ce sont
les **30 phrases GESTE_SIGNATURE/DEFAUT** déjà présentes dans la banque
qu'on a auditées et réécrites cette session, sous forme de tuples
(texte, condition `preferred_moves contient "X"`, tags). `signature_moves`
liste ces 30 (texte, condition, tags), puis une boucle les ajoute une par
une à la feuille "Phrases" via `openpyxl`.

**Cible du fichier** : `PATH = r"C:\Users\omariani\Downloads\banque_de_phrases_simulafoot.xlsx"`
— une copie dans le dossier Téléchargements de l'utilisateur, **pas**
`simulafoot_nlg/data/seed_source/banque_de_phrases_simulafoot.xlsx` (le
fichier suivi par le projet). Modifier ce script et le relancer n'aurait
aucun effet sur le projet sans copie manuelle du résultat.

**Statut** : script local, non suivi par git (`git log` ne retourne
aucun historique pour ce fichier, aucune branche dédiée). Ce n'est pas
"en chantier" — c'est un script d'auteur ponctuel déjà exécuté une fois
(son résultat, ces 30 phrases, est déjà dans la banque suivie par le
projet) et qui n'a plus de raison d'être relancé tel quel (le relancer
dupliquerait les 30 mêmes lignes dans le fichier Téléchargements).

**Couverture** : sans objet — il ne touche aucun joueur, uniquement des
phrases. **Ce fichier ne répond en rien à Option A** (enrichir les
données joueur) malgré son nom.

**Le vrai outil pertinent pour Option A, trouvé en cherchant à côté** :
`scripts/scrape_fminside_attributes.py` (à la racine du projet, modifié/
non commité d'après `git status` — actuellement en chantier, probablement
de ton côté). Sa docstring et son code sont explicites :

- `parse_extras()` récupère poste, taille (`height_cm`), pied faible
  (`weak_foot`) et preferred moves depuis la même section HTML
  (`#player-mobile-info`) d'une fiche joueur fminside.
- **Les preferred moves nécessitent un compte fminside connecté** : le
  code lit `section.player-hidden-attributes`, vérifie un flag `locked`,
  et `write_extras()` n'écrit `moves` que `if not ex.get("locked")` — sans
  cookie de session valide, cette colonne reste "(aucun)" ou inchangée.
- Le cookie se fournit via `--cookie` ou la variable d'environnement
  `FMINSIDE_COOKIE` ; la docstring explique comment le récupérer
  manuellement (F12 dans un navigateur connecté à un compte fminside,
  copier l'en-tête `Cookie` de la première requête).
- **Point non élucidé, à signaler honnêtement** : `height_cm` et
  `weak_foot` sont écrits par le MÊME bloc de code, SANS le même
  verrou `locked` que `moves` — ils devraient donc avoir une couverture
  comparable entre eux. Or `weak_foot` est à 93 % et `height_cm` à
  11,7 %. Je n'ai pas d'explication confirmée par le code à cet écart :
  soit la page fminside elle-même n'affiche pas toujours la taille pour
  les joueurs moins connus (donnée absente à la source, pas un bug du
  scraper), soit une partie des exécutions passées a utilisé une version
  différente du script. Je ne tranche pas sans avoir vu une vraie page
  scrapée — je le signale comme incertitude plutôt que de l'affirmer.

---

## 3. Stratégie données — trois options

### Option A — Enrichir les données
Relancer `scrape_fminside_attributes.py --extras-only --cookie "..."`
avec un cookie de compte fminside valide.
- **Délai** : `--delay` par défaut = 1s/requête ; ~7200 joueurs sans
  `preferred_moves` → **au moins ~2h de temps d'exécution** pour une passe
  complète (probablement plus avec les échecs de correspondance nom/club,
  voir `score_candidate`/`decide`). Faisable en une session si lancé en
  tâche de fond.
- **Risque** : dépend d'un compte fminside actif et de sa capacité à
  tenir ~7200 requêtes sans blocage anti-bot ni expiration de session ;
  risque de correspondance imparfaite (l'algorithme de matching nom/club
  n'est pas garanti à 100 %) ; **n'explique/ne corrige pas forcément
  `height_cm`** (voir incertitude ci-dessus — un cookie valide lève le
  verrou des moves avec certitude, mais l'origine du trou sur la taille
  reste à vérifier).
- **Couverture cible** : optimiste, ~80-93 % si le verrou de connexion
  est bien la seule cause pour `preferred_moves` (cohérent avec les autres
  attributs de la même famille FM) — mais non garanti tant que la cause
  exacte du trou `height_cm` n'est pas confirmée.

### Option B — Assouplir les conditions
Contrainte technique découverte en creusant : la grammaire actuelle
(`parse_condition_atoms`) **ne supporte que la conjonction ("et"), pas de
"ou"** — un vrai fallback ("preferred_moves OU, à défaut, Finishing
élevé") n'existe pas dans le schéma actuel et demanderait une évolution
de `engine/conditions.py` (hors périmètre "pas de code engine/" de ce
tour). La version réalisable sans toucher au moteur : **remplacer** la
condition `preferred_moves` par un attribut bien peuplé qui approxime le
même trait (ex. `preferred_moves contient "Shoots From Distance"` →
`Finishing >= 75`), pas l'ajouter en option.
- **Impact éditorial** : perte de précision — la phrase ne cible plus un
  trait FM spécifiquement tagué, mais un seuil générique. Une partie de
  ce qui rend GESTE_SIGNATURE distinctif (coller à un vrai trait FM)
  s'estompe. Faisable phrase par phrase, jugement au cas par cas sur la
  fidélité du proxy.
- **Délai** : rapide, changement YAML/classeur pur, aucune dépendance
  externe.

### Option C — Accepter le taux faible
Pour GESTE_SIGNATURE spécifiquement : les 30 phrases DEFAUT ne sont PAS
surdimensionnées par rapport à leur population adressable — vérifié
ci-dessus (0 move sans joueur correspondant, pool déjà proche de "1
phrase par trait FM réellement présent chez les 362 joueurs riches").
**Réduire le volume ici n'apporterait presque rien** : le goulot
d'étranglement est la taille de la population (362), pas le nombre de
phrases. Concrètement, "37 → combien" n'a pas de bonne réponse chiffrée :
le scénario fonctionne déjà comme une flaveur niche pour les joueurs
bien documentés, pas comme un scénario universel.

### Recommandation

Pas une option unique — **les trois s'appliquent à des périmètres
différents, pas en concurrence** :

1. **Option C pour GESTE_SIGNATURE tel qu'il existe déjà** : l'accepter
   comme flaveur niche pour les ~362 joueurs riches, ne plus l'étendre
   davantage (chaque nouvelle phrase `preferred_moves`-gated ajoutée là
   n'élargit pas la population atteinte).
2. **Option B pour les scénarios V2 Tier 1 qui doivent toucher tout le
   monde** (TIR_NON_CADRÉ, CARTON_JAUNE) : ne pas répéter l'erreur en
   conditionnant leur volume principal sur `preferred_moves` — préférer
   des attributs à 82-93 % (`Finishing`, `Aggression`) pour le gros du
   pool, garder `preferred_moves` en exception ponctuelle assumée (comme
   BUT/SURNOM "Ambidextre", qui reste correcte parce qu'elle EST censée
   être rare).
3. **Option A en parallèle, sans bloquer la V2 dessus** : le mécanisme
   existe déjà (`--extras-only --cookie`), le tenter est peu coûteux,
   mais son succès sur `height_cm` n'est pas garanti (incertitude non
   résolue en section 2) — donc ne pas compter dessus pour DÉFENSE/CORNER
   tant que ce n'est pas vérifié en pratique.

Je tranche pour la répartition par périmètre ; à toi de confirmer ou
d'ajuster le dosage entre les trois.
