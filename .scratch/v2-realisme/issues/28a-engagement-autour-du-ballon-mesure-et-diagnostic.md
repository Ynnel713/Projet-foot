# 28a: Engagement autour du ballon : mesure et diagnostic par rôle

**Chantier :** `v2-realisme` (audit de réalisme du propriétaire du 21/11/2026, point « effet grappe »). **Priorité :** P1 (premier défaut visible à l'écran). **Catégorie :** mesure.

**Constat vérifié (21/11/2026, script d'audit hors dépôt, 2 matchs moteur à graines `20260923 + 500 + k` contre les 2 matchs Metrica, gardiens exclus, une image par seconde ; ballon mort exclu côté moteur seulement : côté Metrica, seules les images sans ballon détecté sont exclues, les arrêts de jeu où le ballon reste suivi sont comptés ; 2 matchs de chaque côté, images autocorrélées) :**

| Indicateur | Moteur | Metrica |
|---|---|---|
| joueurs de champ (deux équipes) à moins de 10 m du ballon | 4,6 (Q1–Q3 3–6) | 3,4 (2–5) |
| à moins de 15 m | 7,5 (6–9) | 5,9 (4–8) |
| à moins de 20 m | 10,7 (9–13) | 8,6 (6–11) |
| distance moyenne au coéquipier le plus proche | 9,8 m | 11,0 m |
| largeur d'équipe | 41,1 m (36,9–45,6) | 42,1 m (34,9–49,4) |
| part de l'équipe du côté du ballon (ballon hors du couloir central) | 68 % | 69 % |

L'excès est **local** (+ 35 % à 10 m) ; la largeur moyenne et le décalage latéral du bloc sont au niveau du réel. L'écart minimal entre appels existe déjà (`off_ball.SPACING_MIN_M = 8 m`) et ne vise que les appelants. On ne sait pas aujourd'hui **qui** converge : chasseur (`11l`), presseur et suiveurs (`v2-collectif/08`, `27`), soutien, couverture, receveur qui vient au ballon (`v2-socle/01`).

**What to build:**
1. Indicateurs au banc (`scripts/v2_indicators.py`, partagés avec `scripts/suivi_distributions.py` comme au 27b) : joueurs de champ à moins de 10, 15 et 20 m du ballon, par équipe (avec / sans ballon) et au total ; distance au coéquipier le plus proche. Même définition côté moteur et côté suivi réel (SkillCorner toutes positions et Metrica), référence chiffrée écrite dans `docs/INDICATEURS_V2.md` ; la référence qui fait foi est SkillCorner ballon en jeu (possession connue), avec la dispersion entre matchs, avant tout chiffrage du plafond du 28b.
2. Diagnostic : pour chaque joueur à moins de 15 m du ballon, son intention du pas (`cerveau` : chasseur, presseur, suiveur, soutien, appel, couverture, place de référence, receveur) ; part de chaque intention dans l'excès, par zone du ballon.
3. Recommandation chiffrée pour le `28b` (quelles intentions plafonner, de combien).

**Hors de ce ticket :** toute modification du jeu.

**Attributs :** aucun.

**Blocked by:** 27b (livré).

**Bloque :** 28b.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (indicateurs, diagnostic par intention) | 45 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications (référence réelle, rapport) | 30 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : l'intention de chaque joueur est lisible dans `cerveau` sans changer le jeu ; les lecteurs du suivi réel du 27b sont réutilisés tels quels.
Temps machine, non compté : suite complète ; banc de 50 matchs ; lecture des 20 + 2 matchs réels (environ 1 min 10 s).

## Acceptance criteria

- [ ] Mêmes fonctions de mesure pour le moteur et le suivi réel ; références SkillCorner et Metrica écrites (médiane, quartiles)
- [ ] Scène fixe : le compte de joueurs à moins de 10 m est exact (test unitaire)
- [ ] Diagnostic sur 50 matchs : part de chaque intention parmi les joueurs à moins de 15 m, par zone du ballon
- [ ] Recommandation pour le 28b, chiffrée, soumise au propriétaire
- [ ] Jeu inchangé : mêmes empreintes à graine fixée avant / après
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
