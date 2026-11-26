# 01e: Moments dans l'API

**Chantier :** `v2-mise-en-scene` (audit du mode « moments clés », 26/11/2026). **Catégorie :** sérialisation (moteur inchangé).

**Constat vérifié (26/11/2026) :** `MatchTraceOut` et `MatchProgressOut` (`api/routers/v2.py`) servent images, piste du ballon, buts, hors-jeu, situations et journal ; ni occasions, ni tirs typés, ni xG, ni passeur. Le calcul d'un match dure environ 3 minutes ; le rejeu en direct reçoit les données par tranches.

**What to build:**
1. Champ `moments` dans la réponse de `POST /api/v2/matches` et dans la **dernière** réponse de `match_progress` (`done` vrai) : pour chaque mode, la liste des moments (début, fin, ancre, type, tier, score d'intérêt, issue, équipe, joueur, passeur, xG neutre et après frappe de l'ancre si c'est un tir, score avant le moment). Aucun moment n'est envoyé pendant le calcul : les modes ne s'ouvrent qu'une fois le match fini (01f).
2. **Passeur** déduit du journal (dernière passe d'un coéquipier reçue par le buteur dans la chaîne causale du but), sans modification du moteur ; `None` si le but ne suit pas une passe (récupération, rebond, csc). Sert aussi `v2-ecran-match/08c`, `10c`, `17` et `04`.
3. xG et lieu sur les tirs du journal servis à l'écran (surimpressions du `01g`).

**Attributs :** aucun.

**Constantes à proposer :** aucune.

**Blocked by:** 01d.

**Bloque :** 01f ; 04 (règle de déduction du passeur). Alimente `v2-ecran-match/08c` et `10c` (passe décisive à afficher, petit ticket d'écran à ouvrir à la livraison) et remplace la moitié « passeur » du `v2-ecran-match/17`, sans les bloquer.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h** |

Confiance : élevée. Hypothèses : calcul des moments en fin de `_run_job`, coût négligeable devant les 3 minutes du match (à mesurer).
Temps machine, non compté : suite complète (environ 10 min).

## Tests

- Test API : `moments` présent, triés, déterministes à graine fixée (deux appels, mêmes moments) ; absent ou vide pendant le calcul.
- Passeur : trace construite passe puis but : passeur trouvé ; but sur récupération : `None`.
- Charge utile : taille de la réponse avant et après (augmentation rapportée).

## Acceptance criteria

- [ ] `moments` servi en fin de calcul seulement, pour les trois modes, identique sur deux matchs à même graine
- [ ] Passeur juste sur les cas testés, `None` sans passe
- [ ] Temps de calcul des moments et augmentation de la charge utile rapportés
- [ ] Imports par API publique uniquement (ticket 19)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
