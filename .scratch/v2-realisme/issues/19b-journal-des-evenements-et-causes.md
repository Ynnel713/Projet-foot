# 19b: Journal des événements et chaîne de causes

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P0 (avant 18a : attribuer un écart ou tester un enchaînement suppose de savoir quelle action a mené à laquelle). **Catégorie :** architecture.

**Constat vérifié :** `trace.MatchTrace` range les événements par type (`goals`, `offsides`, `restarts`, `fouls`, `shots`, `chances`, `decisions`) sans identifiant ni lien entre eux. `GoalEvent` n'a ni buteur ni dernier toucheur (`BallState.last_toucher` existe mais n'est pas tracé). Un but contre son camp issu d'une déviation (05d) est compté sans être reconnu. Contrôles ratés et pertes de balle ne sont pas des événements. Les cartons, blessures, remplacements, la VAR et les animations à venir ajouteraient chacun une liste de plus.

**What to build:** Chaque événement tracé reçoit un identifiant et, s'il en a une, sa **cause directe** : l'événement qui le précède dans la même action (passe → contrôle raté → perte → tir → arrêt → corner → but). Une liste `MatchTrace.events`, ordonnée et en lecture seule, référence les événements existants sans les remplacer. Ajouts minimaux : contrôle raté, perte de balle (conduite 04b, contrôle, passe interceptée), buteur et dernier toucheur sur chaque but, but contre son camp reconnu. Sérialisé par l'API sans casser les champs actuels. Outil de lecture `scripts/v2_chain.py` : remonter la chaîne d'un but ou d'une occasion.

**Hors de ce ticket :** nouveaux faits de jeu (cartons, blessures, VAR : tickets 09a, 09b, 21) ; affichage à l'écran.

**Attributs :** aucun

**Lien avec l'existant :** exigence de tests de causalité (audit du 10/11/2026, section 11.5) ; base des tickets 21g (VAR) et `v2-mise-en-scene/05`, `06`.

**Blocked by:** 05e (en cours, `match.py` partagé) ; 01f.

**Bloque :** 18a ; 20d ; 21a, 21g, 21i ; `v2-mise-en-scene/05`, `06`. Alimente `v2-mise-en-scene/02` sans le bloquer.

**Status:** à faire

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
- **Unitaires (scène contrôlée) :** tir dévié par un défenseur dans son propre but : but contre son camp, dernier toucheur défenseur
- **Statistiques (séries de matchs) :** 20 matchs : jeu identique à graine fixée ; part des buts dont la chaîne remonte à une récupération, à un coup de pied arrêté, à une erreur

## Acceptance criteria

- [ ] Chaque événement a un identifiant ; cause renseignée quand elle existe
- [ ] Chaîne de la scène de référence retrouvée en entier
- [ ] Buts contre son camp reconnus et tracés
- [ ] Jeu inchangé à graine fixée ; champs actuels de l'API inchangés
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
