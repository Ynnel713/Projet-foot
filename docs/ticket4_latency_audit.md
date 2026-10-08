# Ticket 4 — Diagnostic de la latence et du poids du payload d'animation

Document de travail du **08/10/2026**, sur `HEAD` = `0a35ce4`. **Diagnostic seulement** : aucune ligne de code de production n'a été modifiée, aucune piste n'est implémentée ni décidée. Les mesures viennent d'une instrumentation à l'exécution (enveloppes de fonctions et `cProfile` dans des scripts jetables, **hors dépôt**) appliquée à une archive jetable de `HEAD`.

## 0. Méthode et limites

- **Banc** : serveur `uvicorn` lancé dans le processus de mesure (thread), requêtes HTTP réelles en localhost (`urllib`), sans compression (`Accept-Encoding: identity`). Les durées de chaque fonction sont mesurées par `time.perf_counter` autour de la fonction réelle (enveloppe posée à l'exécution), jamais estimées.
- **Données** : Ligue 1, journée 1 simulée (graine 11), **9 matchs**, tous animés par `GET /api/competitions/{id}/animation` (`max_occasions=None`, comme en production). Le match de **référence** est celui qui a le plus de clips : **FC Toulouse – Paris FC, 19 clips** (aucun des 9 matchs n'atteint 20 clips ; le ticket cite 20 à 22 clips sur un autre match).
- **Bruit de mesure important** : la même requête sur le même match a pris 24,1 s, 16,4 s et 16,5 s selon les passes (charge de la machine, OneDrive, autres processus). Les **parts relatives** (pourcentages) sont fiables ; les durées absolues sont à lire comme une fourchette (16–24 s pour la référence). Un seul échantillon par match dans le tableau §2.3.
- **Hors périmètre** : le temps côté navigateur (parsing JSON, `postMessage`, rendu) n'est pas mesuré ici.

## 1. Cartographie du chemin de génération

| # | Fichier : fonction | Rôle |
|---|---|---|
| 1 | `api/routers/competitions.py` : `get_match_animation` (`GET /{comp_id}/animation`) | point d'entrée ; renvoie un `dict` (pas de `response_model`) |
| 2 | `api/routers/competitions.py` : `_get_or_404`, `_locate_match` | retrouve la compétition (mémoire process, `api/store.py`) et le `Match` (championnat / poule / tableau) |
| 3 | `api/animation.py` : `build_match_animation` | orchestre ; répond `available=False` si non joué, sans compo persistée ou sans temps fort |
| 4 | `ligue1sim/lineup_snapshot.py` : `persisted_lineups` | relit la compo persistée du match |
| 5 | `engine/narrative.py` : `match_result_from` puis `build_timeline` | reconstitue buts, cartons, remplacements réels et intercale les occasions (`Timeline`) |
| 6 | `engine/narrative_player.py` : `build_clips(timeline, max_occasions=None)` | **un `Clip` par événement** ; pour chacun, `_build_clip_frames` |
| 6a | `_build_clip_frames` → `animation/templates.py` `BUILDERS[gabarit]` | construit la `Sequence` (3 à 5 keyframes) |
| 6b | → `animation/sequence_generator.py` `enrich_with_background` | ajoute l'équipe adverse et les dérives tactiques |
| 6c | → boucle `t = 0 … durée`, pas 1/30 s : `animation/motion.py` `interpolate` | **une `FrameState` par image** (positions, vitesses, ballon via `animation/ball.py`) |
| 6d | → `_apply_acceleration_constraint_to_frames` (`animation/physics.py`) | contrainte d'accélération et bornes du terrain |
| 7 | `engine/narrative_player.py` : `clips_to_json` | par clip : `animation/serialize.py` `frame_sequence_to_json` (`json.dumps`), puis `json.loads` pour y ajouter les métadonnées, enfin un `json.dumps` du tableau |
| 8 | `api/animation.py` | **`json.loads(clips_to_json(...))`** : le JSON est reparsé en `dict` |
| 9 | FastAPI / uvicorn | sérialisation de la réponse (JSON compact) et envoi |
| 10 | `ui/src/api/client.js` → `MatchAnimation.jsx` | `fetch`, copie vers l'iframe par `postMessage` |

Le JSON est donc **produit, reparsé puis reproduit** (étapes 7, 8, 9) : trois passes de sérialisation sur 14 à 16 Mo. Aucun cache : chaque appel (y compris le double appel du mode développement React `StrictMode`) recalcule tout.

## 2. Décomposition du coût

### 2.1 Match de référence (FC Toulouse – Paris FC : 19 clips, 4 932 images, 27 joueurs par image)

| Étape (mesurée) | Durée | Part de la requête | Appels |
|---|---|---|---|
| Requête HTTP totale | **24,09 s** | 100 % | 1 |
| ↳ hors handler (sérialisation FastAPI + transfert localhost de 14 Mo) | 0,26 s | 1,1 % | — |
| `build_match_animation` (handler) | 23,83 s | 98,9 % | 1 |
| ↳ `persisted_lineups`, `match_result_from`, `build_timeline` | 0,006 s | 0,0 % | 1 |
| ↳ **`build_clips`** | **21,12 s** | **87,7 %** | 1 |
| ↳↳ **`interpolate`** (une fois par image) | **17,72 s** | **73,6 %** | 4 932 (3,6 ms l'appel) |
| ↳↳ contrainte d'accélération | 3,23 s | 13,4 % | 19 |
| ↳↳ gabarits `BUILDERS[...]`, `enrich_with_background` | 0,043 s | 0,2 % | 19 + 19 |
| ↳ **`clips_to_json`** | **2,27 s** | 9,4 % | 1 |
| ↳↳ `frame_sequence_to_json` (dont `dumps`) | 1,07 s | 4,4 % | 19 |
| ↳↳ `json.loads` par clip (reparsing interne) + `json.dumps` final | 0,54 + 0,60 s | 4,7 % | 19 + 1 |
| ↳ `json.loads` de la réponse (`api/animation.py`) | 0,43 s | 1,8 % | 1 |

**Hotspot : la construction, pas la sérialisation ni le transfert.** `interpolate` + contrainte d'accélération = 87 % du temps ; toute la chaîne JSON (3 passes) ≈ 12 % ; le transfert en localhost est négligeable (un `jsonable_encoder` isolé, refait à part sur le même objet, coûte 3,3 s, mais ce n'est visiblement pas ce qui est exécuté en production : le temps réel hors handler n'est que de 0,26 s).

### 2.2 Où passe le temps dans `interpolate` (cProfile, même match)

Le profileur gonfle les petites fonctions (35 s au lieu de 17–24 s) ; seules les proportions comptent :
- `_raw_position_at` : 399 492 appels, soit **81 par image = 27 joueurs × 3** (position, et position ±ε pour estimer la vitesse par **différence finie**), avec `_ease_progress` (385 520 appels) et les courbes de Bézier : **≈ 45 % d'`interpolate`**.
- `_apply_avoidance` : 4 932 appels, **6,96 M de calculs de distance** (351 paires × 4 passes par image, en Python pur) : **≈ 29 %**.
- `_background_position_at` (dérives des joueurs « de fond ») et les `dataclasses.replace` : le reste.

### 2.3 Les 9 matchs

| Match | Clips | Images | Requête | s / clip | s / 1 000 images | Réponse |
|---|---|---|---|---|---|---|
| Auxerre – Rennes | 15 | 3 505 | 16,8 s | 1,12 | 4,8 | 9,8 Mo |
| Monaco – Brest | 16 | 4 443 | 39,2 s | 2,45 | 8,8 | 12,4 Mo |
| Angers – Strasbourg | 16 | 3 677 | 19,0 s | 1,19 | 5,2 | 10,4 Mo |
| Troyes – Lens | 11 | 2 550 | 14,4 s | 1,31 | 5,7 | 7,0 Mo |
| Lorient – PSG | 17 | 4 595 | 27,7 s | 1,63 | 6,0 | 12,2 Mo |
| **Toulouse – Paris FC** | **19** | **4 932** | **24,1 s** | 1,27 | 4,9 | **14,1 Mo** |
| Lille – Marseille | 11 | 2 355 | 7,4 s | 0,67 | 3,1 | 6,5 Mo |
| Le Havre – Lyon | 19 | 4 724 | 16,0 s | 0,84 | 3,4 | 13,2 Mo |
| Le Mans – Nice | 18 | 4 170 | 15,1 s | 0,84 | 3,6 | 11,5 Mo |

Le **poids est quasi proportionnel aux images** (2 660 à 2 860 octets par image) ; le **temps varie du simple au triple par image** (3,1 à 8,8 s / 1 000 images), ce qui ne s'explique pas par le seul bruit de mesure (échantillon unique) : une part dépend probablement des données (nombre de paires en évitement). Non tranché.

## 3. Décomposition du poids (match de référence : 14 107 725 octets)

- **19 clips**, **4 932 images** au total (par clip : min 135, médiane 245, max 453 ; durées 4,5 à 15,1 s), cadence **30 images/s** (`_FPS = 30`).
- **27 joueurs par image** dans les 19 clips : 11 adversaires + **16 joueurs de l'équipe qui marque** (numéros 1 à 16 : 11 titulaires + **5 remplaçants** placés sur le terrain, ex. n° 12 en (0,18 ; 0,48), et animés comme les autres).
- **Keyframes** : le payload ne contient pas de keyframes, seulement des images échantillonnées à 30/s. Chaque `Sequence` n'en définit que **3 à 5** (médiane 4) ; tout le reste est interpolé côté Python puis envoyé image par image.
- **Taille moyenne** : 2 860 octets par image, soit ~105 octets par joueur et par image.

| Catégorie | Octets | Part |
|---|---|---|
| **Identité du joueur répétée à chaque image** (`id`, `team`, `numero`, `active`) | 7 570 424 | **53,7 %** |
| **Positions des joueurs** (`x`, `y`) | 5 589 748 | **39,6 %** |
| Ballon (`x`, `y`, `z`, `spin`, `owner`) | 479 245 | 3,4 % |
| Structure JSON (accolades, virgules, clés d'image) | 335 970 | 2,4 % |
| Temps `t` des images | 108 543 | 0,8 % |
| Noms des joueurs (`player_names`, **une fois par clip**) | 13 447 | 0,1 % |
| Métadonnées de clip | 8 377 | 0,1 % |
| Évènements d'intervalle | 1 971 | 0,0 % |

Étapes de taille : `clips_to_json` brut **15 786 487** octets (séparateurs par défaut `", "` / `": "`) → après `json.loads` puis sérialisation compacte **14 107 725** (−10,6 %) → réponse HTTP **14 107 725** (aucune compression). L'objet Python « clips » (19 clips, 4 932 images × 27 joueurs = 133 164 états de joueur) n'a pas d'équivalent en octets mesuré.

**Redondances relevées**
- **Noms** : déjà envoyés **une seule fois par clip** (`player_names`, 0,1 %) ; mais l'**`id` texte de chaque joueur (ex. `home_rw0`) est répété à chaque image**, avec `team`, `numero` et `active`, qui sont **constants sur tout un clip** pour chaque joueur (vérifié) : 53,7 % du poids est de l'identité répétée.
- **Joueurs immobiles** : **0,4 %** seulement des positions sont identiques à l'image précédente (515 sur 132 651). Tous les joueurs dérivent en continu (dérives tactiques des joueurs de fond), donc **un codage « uniquement ce qui bouge » ne gagne rien** (testé : plus gros qu'une simple table de référence).
- **Précision** : `x` et `y` sont des flottants complets (31 caractères en moyenne pour la paire) alors que 4 décimales (≈ 1 cm) suffisent à l'œil.
- `ball.owner` est répété sur 4 726 images sur 4 932.

## 4. Pistes d'optimisation (non implémentées)

Les six premières sont celles demandées ; les gains « Mesuré » viennent du payload réel (transformation simulée hors dépôt), les autres sont des estimations grossières.

| # | Piste | Gain attendu | Risque | Complexité |
|---|---|---|---|---|
| 1 | **Cache mémoire par match** (clé : compétition + match + libellé) | **Mesuré** : 2e appel **16,5 s → 0,29 s**. 1er appel inchangé. Couvre aussi le double appel du mode développement | invalidation si la compétition change (un match joué est immuable) ; mémoire ≈ 14 Mo de JSON par match, bien plus en objets Python → LRU borné ; deux requêtes simultanées calculent deux fois sans verrou | faible (~20 lignes + tests) |
| 2 | **Compression gzip** de la réponse (`GZipMiddleware`) | **Mesuré** : 14,11 → **2,07 Mo (−85 %)**, compression 0,58 s par réponse (à mettre en cache avec le payload). Aucun effet sur les 24 s de calcul ; gros effet hors réseau local (tunnel, téléphone) | CPU serveur ; sans effet sur la mémoire du navigateur (le JSON décompressé reste de 14 Mo) | très faible (1 ligne) |
| 3 | **15 images/s au lieu de 30** | **Mesuré** : poids −50 % (7,10 Mo). **Estimé** : temps de construction ~−45 % (`interpolate` et contrainte appelés deux fois moins) | fluidité : le lecteur interpole déjà linéairement entre deux images (`lerp`), donc probablement acceptable, mais la contrainte d'accélération est réglée pour 1/30 s ; tir à 35 m/s = 2,3 m par image ; tests et captures à refaire | faible (constante `_FPS`) à moyenne (recalage de la contrainte, du cap, de la détection du but) |
| 4 | **Ne transmettre que les positions qui changent** | **Mesuré : aucun gain** (0,4 % de positions identiques ; la variante « table + positions changées » fait 6,10 Mo contre 5,50 Mo pour la table seule). Variante radicale : envoyer seulement les 3–5 keyframes et interpoler dans le navigateur : poids ÷ 100 et 87 % du calcul déporté, mais il faut **porter `motion.interpolate`, `ball`, l'évitement et la contrainte en JavaScript** | fidélité visuelle et déterminisme à reprouver ; double maintenance | très élevée (variante radicale) |
| 5 | **Table de référence** : `id`/`team`/`numero`/`active` envoyés une fois par clip, images = `[t, balle, [[x, y], …]]` | **Mesuré** : 14,11 → **5,50 Mo (−61 %)** sans compression ; avec gzip seulement 2,07 → 1,81 Mo (gzip déduplique déjà). Réduit aussi le parsing JSON et la copie `postMessage` côté navigateur | **changement de protocole** (`version` 1 fermé : bump + `canvas.html`, `matchAnimation.js`, `serialize.py`, tests) | moyenne |
| 6 | **Limiter `max_occasions`** (15 ou 12 clips) | **Mesuré** : 15 premiers clips = 11,4 Mo (−19 %), 12 = 8,4 Mo (−40 %) ; temps ≈ proportionnel | **élevé** : `max_occasions` retient les *premiers* événements chronologiques, donc des buts tardifs peuvent disparaître ; il faudrait sélectionner par importance (tous les buts d'abord) | faible (limiter) à moyenne (sélection par importance) |

**Pistes complémentaires issues du diagnostic** (hors des six demandées) :

| # | Piste | Gain attendu | Risque | Complexité |
|---|---|---|---|---|
| 7 | **Réduire le coût d'`interpolate`** (74 % du temps) : vitesse analytique ou réutilisée au lieu de 3 évaluations par joueur ; évitement limité aux paires proches (ou vectorisé) | estimé −40 à −70 % du temps du premier appel, **le seul levier sur la latence à froid** avec les pistes 3 et 8 | touche `animation/motion.py` (moteur de rendu, protégé par des tests de déterminisme et d'empreinte) ; régressions visuelles | moyenne à élevée |
| 8 | **Ne pas animer les 5 remplaçants** de l'équipe qui marque (27 → 22 joueurs par image), sauf si l'un d'eux est le protagoniste du clip | **−18,5 %** de poids et de temps (estimation arithmétique, 5/27) ; corrige aussi un défaut visuel probable : des remplaçants dessinés sur le terrain | change le rendu (joueurs n° 12 à 16 disparaissent) ; cas du buteur remplaçant à préserver | faible à moyenne |
| 9 | **Arrondir `x`, `y`, `z`, `spin`** (4 décimales) | **Mesuré** : −21 % sans compression (11,13 Mo) ; **avec gzip : 2,07 → 0,50 Mo (−76 %)** | quantification ≈ 1 cm, invisible ; tests à égalité stricte de flottants | très faible |

**Combinaisons mesurées** : arrondi + table de référence (30 images/s) = **2,52 Mo (17,9 %)**, gzip **0,38 Mo** ; arrondi + table + 15 images/s = **1,29 Mo (9,2 %)**, gzip **0,24 Mo**.

## 5. Essai à blanc du cache mémoire (copie jetable, non commité)

Match de référence, requêtes HTTP successives sur le même serveur :

| Scénario | 1er appel | 2e appel |
|---|---|---|
| Sans cache | 16,38 s | 16,51 s (réponse identique octet pour octet) |
| Cache du `dict` retourné par `build_match_animation` | 19,25 s | **0,29 s** (sérialisation FastAPI et transfert localhost de 14 Mo compris) |

Une variante « cache des octets sérialisés » n'a pas pu être exercée (mon remplacement du point d'entrée n'a pas pris effet : 2e appel à 18,25 s) ; elle n'est pas nécessaire, le cache du `dict` étant déjà quasi instantané. **Le cache ne réduit pas la latence du premier appel** (16 à 24 s) : seules les pistes 3, 7, 8 (et partiellement 6) agissent sur le calcul initial.

## 6. Observations annexes

- Comparaison avec la mesure initiale du ticket (9,5 Mo, 22 clips, 13,6 s) : non comparable (autre match, autre état du payload) ; aujourd'hui 0,59 à 0,77 Mo par clip selon la durée des clips.
- Depuis la Phase 5, le payload porte en plus `ball.owner` et `metadata.player_names` (+0,74 %).
- Le plafond de 5 % de surcoût de rendu de la Phase 5 concerne le navigateur, pas ce diagnostic.

## 7. Recommandations du Chef d'Orchestre

*À remplir dans une deuxième passe, après lecture du diagnostic. Ce document est un document de travail, pas une décision.*

## 8. Reproductibilité

Scripts de mesure jetables (instrumentation par enveloppes de fonctions, serveur `uvicorn` en thread, `cProfile`, analyse du payload réel, essai de cache), écrits dans un dossier temporaire **hors dépôt** et appliqués à une archive jetable de `HEAD` ; non commités. Graine 11, Ligue 1, journée 1.
