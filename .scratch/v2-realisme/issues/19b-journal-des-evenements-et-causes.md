# 19b: Journal des événements et chaîne de causes

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P0 (avant 18a : attribuer un écart ou tester un enchaînement suppose de savoir quelle action a mené à laquelle). **Catégorie :** architecture.

**Constat vérifié :** `trace.MatchTrace` range les événements par type (`goals`, `offsides`, `restarts`, `fouls`, `shots`, `chances`, `decisions`) sans identifiant ni lien entre eux. `GoalEvent` n'a ni buteur ni dernier toucheur (`BallState.last_toucher` existe mais n'est pas tracé). ~~Un but contre son camp issu d'une déviation (05d) est compté sans être reconnu.~~ Corrigé le 10/11/2026 (architecte) : un but contre son camp est **impossible** aujourd'hui ; un tir contré ou arrêté perd son vol (`match._blocked`, arrêt), et un ballon libre qui franchit la ligne entre les poteaux devient corner ou sortie de but (`restart.award`), jamais but. Le reconnaître est un changement de jeu : ticket `05i`. Contrôles ratés et pertes de balle ne sont pas des événements. Les cartons, blessures, remplacements, la VAR et les animations à venir ajouteraient chacun une liste de plus.

**What to build:** Chaque événement tracé reçoit un identifiant et, s'il en a une, sa **cause directe** : l'événement qui le précède dans la même action (passe → contrôle raté → perte → tir → arrêt → corner → but). Une liste `MatchTrace.events`, ordonnée et en lecture seule, référence les événements existants sans les remplacer. Ajouts minimaux : passe, contrôle raté, perte de balle (conduite 04b, contrôle, passe interceptée, tacle), contre, arrêt, buteur et dernier toucheur sur chaque but, champ « contre son camp » (faux tant que le `05i` n'est pas livré). Sérialisé par l'API sans casser les champs actuels (tous les événements, passes comprises, en fin de match comme les décisions).

**Règle de cause (architecte, 10/11/2026)** : un curseur sur le dernier événement du ballon ; chaque événement prend pour cause ce curseur puis le devient ; seul l'engagement ouvre une chaîne (cause vide). La chaîne traverse les changements d'équipe et les ballons morts. Une perte n'est émise qu'au toucher d'un joueur quand le dernier événement est une passe, un contrôle raté ou une touche trop longue de l'autre équipe (pas après un arrêt ou un contre).

**Hors de ce ticket :** nouveaux faits de jeu (cartons, blessures, VAR : tickets 09a, 09b, 21) ; affichage à l'écran ; outil `scripts/v2_chain.py` et origine des buts (`19e`) ; but sur ballon dévié et but contre son camp reconnu (`05i`, change le jeu). **Découpé le 10/11/2026** sur recommandation de l'architecte, validée par délégation du propriétaire.

**Attributs :** aucun

**Lien avec l'existant :** exigence de tests de causalité (audit du 10/11/2026, section 11.5) ; base des tickets 21g (VAR) et `v2-mise-en-scene/05`, `06`.

**Blocked by:** 05e (livré) ; 01f (livré).

**Bloque :** 18a ; 19e ; 05i ; 20d ; 21a, 21g, 21i ; `v2-mise-en-scene/05`, `06`. Alimente `v2-mise-en-scene/02` sans le bloquer.

**Status:** livré (10/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 55 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : les événements existants ont tous un instant et un acteur ; la cause se lit dans l'état du ballon.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** passe en retrait, contrôle raté du gardien, ballon perdu, tir, but : la chaîne remontée depuis le but contient ces cinq maillons dans l'ordre
- **Unitaires (scène contrôlée) :** tir contré : le contre est tracé avec le contreur, cause le tir, aucun but
- **Statistiques (séries de matchs) :** 20 matchs : jeu identique à graine fixée (empreinte des champs d'avant le ticket) ; chaque but a un buteur et une chaîne qui remonte à un engagement

## Acceptance criteria

- [ ] Chaque événement a un identifiant ; cause renseignée quand elle existe
- [ ] Chaîne de la scène de référence retrouvée en entier
- [ ] Buteur et dernier toucheur sur chaque but ; champ « contre son camp » présent (reconnaissance au `05i`)
- [ ] Jeu inchangé à graine fixée ; champs actuels de l'API inchangés
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 10/11/2026, architecte (`simulafoot-architect`) consulté avant le code : règle de cause, points d'accroche, découpage en 19b, `19e` (lecture de chaîne, origine des buts) et `05i` (but sur ballon dévié, change le jeu) ; constat corrigé : un but contre son camp est impossible aujourd'hui. Recommandations validées par délégation du propriétaire. Estimation du périmètre réduit inchangée (2 h 05).
- 10/11/2026, implémentation : `trace.TraceEvent` (identifiant, minute, type, équipe, joueur, cause, précision, autre joueur), `trace.EventLog` (cause = dernier événement du ballon ; l'engagement ouvre une chaîne), `trace.chain`, `MatchTrace.events` ; `GoalEvent` reçoit `scorer`, `last_toucher`, `own_goal` (valeurs par défaut, champs existants intacts). Journal porté par le ballon (`BallState.log`, vide hors match tracé) plutôt que passé en paramètre à sept fonctions ; branché dans `match.py` sur 11 types : passe, contrôle raté, perte (passe interceptée, contrôle, conduite, tacle), touche longue, tir (dévissé et penalty compris), contre, arrêt, but, remise (engagement, touche, corner, sortie de but, coup franc, penalty), faute (sifflée ou avantage acquis), hors-jeu. Écritures seulement, aucun tirage ajouté ni déplacé ; le type « tir » est importé sous `TIR_EVENT` (`TIR` est le flux aléatoire des tirs). API : `TraceEventOut`, `MatchTraceOut.events`, `MatchProgressOut.events` en fin de match, `GoalEventOut` étendu ; champs actuels inchangés.
- Défaut trouvé par la mesure et corrigé : à la mi-temps, `simulate_match` recrée le ballon ; le journal n'y était pas rebranché, la 2e période n'était pas tracée (buts compris). Test `test_the_log_covers_both_halves_and_every_goal`.
- Mesures : 20 matchs à graine fixée, empreinte des seuls champs d'avant le ticket (ticks, listes d'événements, `(minute, équipe)` des buts) : **20 sur 20 identiques avant et après** (`.scratch/v2-realisme/mesures/19b-empreintes-avant.txt`, `-apres.txt`). Sur ces 20 matchs (`19b-buts.txt`) : 108 buts, 108 événements « but », buteur sur chacun, chaque chaîne remonte à un engagement, identifiants croissants et causes antérieures, aucun but contre son camp ; environ 1 900 événements par match dont 650 à 880 passes. Les chaînes sont longues (jusqu'à 596 maillons) : elles vont de l'engagement au but ; le 19e classera l'origine. Suite complète : 2 714 passés, 14 désélectionnés (2 707 + 7, `19b-suite.txt`).
- Durée : estimée 125 min, réelle environ 150 min (analyse 30, développement 55, tests 35, intégration 30 ; estimée, non chronométrée), + 20 %. Temps machine hors total : 4 × 8 min de matchs, 2 suites complètes (24 et 33 min).
- 10/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS, QC VALIDÉ, clôture VALIDÉ. Réserve A1 acceptée par délégation du propriétaire (« Considère que je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026) : la faute avec avantage est écrite au règlement de l'avantage (minutes non croissantes, faute qui peut avoir un but pour cause) ; correction reportée au `19e`, avant la lecture des chaînes. Facultatifs : A2, arrêt non écrit sur penalty manqué (au `v2-attributs-restants/02a`) ; A3, `MatchTrace.events` modifiable (événements gelés). Réserve de forme du QC : le test de la mi-temps dépend d'une graine et de deux clubs précis.
