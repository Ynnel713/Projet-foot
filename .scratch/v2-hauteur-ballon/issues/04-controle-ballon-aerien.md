# 04: Qualité du contrôle d'un ballon aérien ou rebondissant

**What to build:** Le ticket 03 décide QUI peut toucher un ballon selon sa hauteur (tranches pied, corps, tête, mains) et renvoie la qualité du geste aux tickets existants ; or le contrôle (`v2-collectif/31`, `possession.control_difficulty`) ne connaît qu'un ballon au sol (vitesse et pression). Ici : la difficulté d'un contrôle dépend de la partie du corps (pied, cuisse, poitrine ; tête : `v2-attributs-restants/01`), de la hauteur et de la vitesse verticale du ballon (ballon qui tombe, qui rebondit), sur la même échelle que les autres difficultés ; First Touch règle la réussite comme au sol, Technique le geste difficile (règle anti double comptage de `docs/CARTE_ATTRIBUTS_V2.md`). Un contrôle raté laisse le ballon libre selon sa hauteur (rebond, ticket `v2-realisme/14c` s'il est livré).

Revue du réalisme du 12/11/2026 (demandée par le propriétaire) : manque relevé, aucun ticket ne couvrait la qualité du contrôle aérien.

**Hors de ce ticket :** qui touche le ballon (03) ; volée et demi-volée en tir (`v2-collectif/34d`) ; duel aérien et tête (`v2-realisme/15a` à `15c`).

**Blocked by:** 03 (interception selon la hauteur) ; `v2-collectif/31` (contrôle orienté au sol).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 30 min |
| Développement | 45 min |
| Tests | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible (chiffres réels à trouver). Temps machine, hors total : séries de 50 matchs, suite complète.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scènes : même ballon au sol, à hauteur de cuisse, de poitrine, rebondissant ; difficulté croissante, First Touch 99 contre 11
- [ ] Part des contrôles ratés par hauteur mesurée sur 50 matchs ; table de passe du `v2-realisme/18g` remesurée si elle bouge
- [ ] Déterminisme à graine fixée ; suite complète comparée à l'attendu de `CLAUDE.md`

## Comments
