# 01: Buts et lecteur (socle des moments et lecteur des modes)

**Status:** découpé (26/11/2026, audit du mode « moments clés », décisions du propriétaire du 26/11/2026) en 01a à 01g. Ce fichier garde la vue d'ensemble ; le travail et les critères sont dans les sous-tickets.

**Principe (décision du propriétaire, 26/11/2026) :** les modes de visionnage sont un **filtre de lecture** sur la trace déjà produite par le moteur, pas une seconde simulation. Le moteur n'est pas modifié, à une exception près accordée pour 01a (instrumentation en lecture seule, voir ce ticket).

**Constat vérifié (26/11/2026) :**
- **Aucun rejeu ni snapshot à prévoir.** La trace contient toutes les images des joueurs (`MatchTrace.ticks`) et le ballon à chaque pas du moteur (`ball_track`), envoyées à l'écran. Un moment est un intervalle `[début, fin]` de cette trace. La trace est reproductible à graine fixée (D-V06, D-V13 ; SHA-256 identiques à `v2-ecran-match/00`), sans garantie entre deux versions du moteur : un moment se calcule toujours sur la trace du même calcul, jamais à partir d'une graine stockée.
- **Journal disponible** (`v2engine/trace.py`) : `TraceEvent` avec cause (`chain()` remonte la chaîne de l'action), `ShotEvent` (lieu, qualité, issue, origine, `xg`, `post_shot_xg`), `ChanceEvent` (début, pic, fin, danger, issue ; 7,7 par match, 52 % sans tir, mesure du 28c), `FoulEvent` (gravité, issue dont penalty), `RestartEvent`, `OffsideEvent`, `GoalEvent` (buteur, csc).
- **Manques** : pas de cartons (`v2-attributs-restants/09a`), pas de VAR (`v2-realisme/21g`, `21h`), pas de remplacements (`v2-coach-et-gestion-de-match/05a`) ; pas de passeur dans `GoalEvent` ; l'API ne sert ni les occasions, ni les tirs typés, ni l'xG (`TraceEventOut` n'a que id, minute, type, équipe, joueur, cause, détail, autre) ; réserves A1 et A2 du `v2-collectif/28c` ouvertes.

**Décisions du propriétaire (26/11/2026) :**
1. Le chantier `v2-mise-en-scene` porte les modes ; pas de chantier séparé.
2. **Résumé** (« Temps forts » dans le sélecteur d'EM-19) : **10 à 15 minutes à ×1**. **Moments clés** : le mode court (Tier 1 seulement). **Buts** : les buts seulement.
3. Première version sans cartons rouges ni VAR (absents du moteur) ; ils entrent au Tier 1 à la livraison de `09a`, `21g`, `21h`.
4. 01a modifie `v2engine/occasion.py` (et l'étiquette d'origine dans `match.py`) par exception : lecture seule, jeu inchangé, seule la trace change.
5. Vitesses existantes (×1, ×1,5, ×2, ×8, ×32, EM-09) : rien à ajouter, le lecteur saute d'un moment à l'autre.
6. Calcul côté serveur (Python, testé) ; l'écran ne fait que lire.
7. Validation en deux passages : `07a` maintenant, `07b` après la calibration (`v2-collectif/22a` à `22c`), parce que les poids bougeront.

**Trois tiers :**
- **Tier 1, toujours montré** : buts, penalties, grosses occasions (`ChanceEvent`) ; plus tard cartons rouges et décisions VAR.
- **Tier 2, si le budget le permet** : tirs dangereux hors grosse occasion, arrêts décisifs, coups francs directs cadrés, belles constructions (quand `v2-realisme/31b` les mesure), poteaux (quand `v2-collectif/35c` existe). La contre-attaque n'est pas un type : c'est un modificateur du score d'intérêt (01b).
- **Tier 3, en surimpression seulement**, jamais comme moment : fautes, corners, hors-jeu, puis cartons jaunes et remplacements.

**Pièges à éviter, pris en charge par les sous-tickets :** construction molle (01c : la fenêtre démarre au début réel de l'action, lu dans `chain()`) ; double comptage but + tir + occasion, faute + penalty, tir repoussé + second tir (01c : un seul moment) ; contexte absent avant un moment (01f : carton de contexte).

## Sous-tickets

| # | Titre | Bloqué par | Estimation |
|---|---|---|---|
| 01a | Séquences d'occasion fiables (réserves 28c A1, A2) | — | 1 h 30 |
| 01b | Taxonomie et score d'intérêt | 01a | 1 h 45 |
| 01c | Fenêtres des moments | 01b | 1 h 45 |
| 01d | Sélection sous budget et modes côté serveur | 01c | 1 h 15 |
| 01e | Moments dans l'API | 01d | 1 h |
| 01f | Lecteur : modes, enchaînement, contexte | 01e, `v2-ecran-match/19` | 2 h |
| 01g | Lecteur : barre de progression et surimpressions | 01f | 1 h 45 |

Suite : `02` (mode Moments clés, 1 h), `03` (mode Résumé, 1 h 45), `07a` (validation, 1 h 30), `07b` (second passage après la calibration, 50 min). Total du chantier révisé : **16 h 05** de travail effectif.

**Passeur :** les tickets qui attendaient « le passeur dans la trace » de ce ticket (`v2-ecran-match/08c`, `10c`, `17`, `04`) le trouvent dans la réponse de l'API au `01e`, déduit du journal, sans modification du moteur.

**Mode Buts :** les moments de type but (01d) lus par le lecteur (01f). Pas de ticket à part.

## Comments

- 26/11/2026 : périmètre d'origine (trace enrichie, moments serveur, mode Buts, lecteur, sans spoiler) repris intégralement dans 01a à 01g. Le point 1 d'origine (buteur et passeur écrits par le moteur) est remplacé par une déduction côté serveur au `01e`, conformément au principe du filtre de lecture.
