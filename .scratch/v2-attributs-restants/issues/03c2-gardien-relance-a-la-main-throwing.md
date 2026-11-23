# 03c2: Gardien : relance à la main (Throwing)

**Découpé du ticket `03c` le 22/11/2026.** Gardien de référence : Throwing 55, médiane des 50 gardiens notés de Ligue 1 de la base (de 25 à 80).

**What to build:** état « ballon en main » (gardien qui a capté un tir, ou pris dans sa surface un ballon qui ne vient pas d'une passe volontaire d'un coéquipier) ; avec le ballon en main, une passe vers un coéquipier à portée de bras se joue à la main : Throwing remplace Passing dans sa précision, portée selon Throwing ; au-delà, dégagement au pied (Kicking, `03c1`). Le geste préféré « Uses Long Throw To Start Counter Attacks » est branché au `05a`.

**Attributs :** Throwing.

**Blocked by:** `03c1`.

**Bloque :** `05a` (ligne « Gardien ») ; `v2-collectif/22a`.

**Status:** livré (23/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 20 min |
| Développement | 30 min |
| Tests | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Temps machine, non compté : série réelle de 50 matchs, deux séries forcées de 30 matchs (Throwing 30 et 80), environ 1 h 45 ; suite complète (20 min).

**Constantes** (proposées au propriétaire le 23/11/2026, délégation permanente « Je valide automatiquement toutes tes recommandations et les avis d'expert ») : référence 55 ; ballon en main : capté sur un arrêt (ou penalty arrêté), ou contrôlé dans sa surface quand la dernière passe n'est pas de son équipe (règle de la passe en retrait) ; il ne l'est plus dès qu'il n'a plus le ballon ; lancer : passe au sol vers un partenaire à portée de bras, précision Throwing à la place de Passing (même difficulté qu'une passe au sol) ; portée 30 m à 55 + 0,3 m par point, bornée à 20-40 m (21 m à 25, 37,5 m à 80) ; choix du receveur inchangé (ADR 0002 ; la valeur d'une passe lit la même précision que l'exécution). Repères réels : lancer d'un gardien de haut niveau, 30 à 40 m (ordre de grandeur) ; relation note-distance non trouvée.

**Critères chiffrés** (posés avant le code) : gardien ballon au pied, ou sans note : comportement d'avant (scène) ; scène : précision d'un lancer croissante de Throwing 30 à 80, Passing sans effet sur elle ; portée : partenaire à 34 m lancé à 80, pas à 55 ; un long ballon en l'air depuis la main reste un dégagement (Kicking) ; un joueur de champ ne lance jamais ; match : jamais en main sans avoir le ballon, en main au moins une fois en 15 minutes ; séries forcées (30 matchs, mêmes graines) : lancers mesurables (au moins 1 par gardien et par match), longueur moyenne des lancers plus grande à 80 qu'à 30 ; série réelle : buts par match avec intervalle.

## Acceptance criteria

- [x] Constantes produit et critères chiffrés validés par le propriétaire avant le code (délégation)
- [x] Throwing : distance et précision des relances à la main mesurablement liées à l'attribut (scène ; séries forcées : longueur 9,2 → 11,4 m, part gardée 93,8 → 98,9 %)
- [x] Ballon au pied ou passe en retrait : Passing, comme avant ; jamais en main sans le ballon (match de 15 minutes)
- [x] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Résultats (23/11/2026)

- Code : `PlayerState.in_hands` (tenu d'un pas à l'autre par `movement.step`) ; mis à vrai par `match._keeper_save` (capté), le penalty arrêté et le contrôle du gardien dans sa surface quand la dernière passe n'est pas de son équipe ; remis à faux dans la boucle du match dès qu'il n'a plus le ballon ; `possession.throwing` (référence 55), `throw_range_m`, `keeper_throw` ; `pass_accuracy_probability` lit Throwing pour un lancer. Commentaire de portée de Kicking corrigé (réserve A3 du `03c1`).
- Scènes (`tests/test_v2engine_relance_a_la_main.py`, 5 cas) : référence et constantes ; précision croissante de 30 à 80, Passing sans effet, ballon au pied inchangé, partenaire à 34 m lancé à 80 et pas à 55, long ballon depuis la main = dégagement (Kicking), joueur de champ jamais ; arrêt capté = ballon en main ; ballon d'un adversaire pris dans sa surface en main, passe en retrait non ; en match (15 minutes), jamais en main sans le ballon, en main au moins une fois ; tenu d'un pas à l'autre. Garde des attributs : scène « relance à la main » (Throwing 11 contre 99, divergence trouvée).
- Séries (mêmes graines ; avant : `03c1-reel`, code de `1659620`) :

| Série | Buts/match | Lancers/gardien/match | Longueur des lancers (90e centile) | Lancers gardés |
|---|---|---|---|---|
| avant (50 matchs) | 4,42 | — | — | — |
| réelle (50 matchs) | 4,62 | 1,22 | 10,5 m (17,0) | 97,5 % |
| Throwing forcé à 30 (30 matchs) | 4,73 | 1,08 | 9,2 m (19,0) | 93,8 % |
| Throwing forcé à 80 (30 matchs) | 4,17 | 1,45 | 11,4 m (18,4) | 98,9 % |

  Écart apparié des buts : réelle + 0,20 [− 0,22 ; + 0,62] ; 80 contre 30 : − 0,57 [− 1,41 ; + 0,27], dans le bruit. Observation : les lancers restent courts (10,5 m en moyenne) ; la décision préfère le partenaire proche et libre, les relances longues partent au pied (4,2 par gardien et par match) ; le lancer long vers un ailier (30-40 m) et le geste préféré « Uses Long Throw To Start Counter Attacks » sont l'affaire du `05a` et du choix de la relance (`v2-collectif/15e`).
- Suite complète : 3 565 passés, 0 ignoré, 14 désélectionnés (3 559 + 6 : 5 cas nouveaux, 1 dans la garde des attributs). Déterminisme : matchs 0 et 1 rejoués deux fois, mêmes empreintes (`cbef1fc2…`, `8ce66d1e…`).
- Durée réelle : environ 1 h 50 (analyse 20, développement 35, tests 30, intégration et vérifications 25), + 5 % ; code préparé pendant les séries des tickets précédents ; un défaut trouvé avant les mesures (état « en main » perdu à chaque pas par `movement.step`, corrigé et testé) ; à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : séries (50 + 30 + 30 matchs, environ 1 h 45), suite complète (16 min).

## Comments

- 23/11/2026, passage 1 : expert APPROVED ; QC VALIDÉ ; clôture VALIDÉ. Aucune anomalie bloquante. Améliorations facultatives de l'expert : A1, un gardien en main peut conduire le ballon hors de sa surface et lancer (rare, non observé) : remettre `in_hands` à faux hors de sa surface, ticket de suite à ouvrir si la conduite du gardien devient fréquente ; A2, lancers courts et rares (1,2 par gardien et par match, 10,5 m) : au `05a` et au `v2-collectif/15e`. Réserves du QC, non bloquantes : date du commentaire de Kicking (23/11, date de la délégation appliquée au 03c1), buts 80/30 dans le bruit, critère d'au moins un lancer tenu en moyenne.
