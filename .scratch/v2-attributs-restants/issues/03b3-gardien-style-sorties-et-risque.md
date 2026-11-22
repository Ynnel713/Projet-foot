# 03b3: Gardien : style (Rushing Out, Eccentricity)

**Découpé du ticket `03b` le 22/11/2026** (décision du propriétaire). Gardien moyen : médiane des gardiens de Ligue 1 de la base (Reflexes 75, One on Ones 75, Handling 60) ; un gardien sans note (effectif synthétique, copie neutre de l'xG) vaut le gardien moyen.

**What to build:** placement et sorties hors de la surface (Rushing Out, tendance : hauteur de placement, marge de sortie `gardien.RUSH_MARGIN_S`, distance maximale `RUSH_MAX_FROM_GOAL_M`), goût du risque (Eccentricity, tendance : sorties inattendues). Tendances : elles changent le style, jamais le niveau. Rushing Out est absent de la base (60 pour tous) : effet visible seulement avec des données enrichies (`06`).

**Attributs :** Rushing Out, Eccentricity.

**Blocked by:** `03b1`.

**Bloque :** `10b` (lob et dribble du gardien) ; `v2-coach-et-gestion-de-match/04` ; `v2-collectif/22a`.

**Status:** découpé (22/11/2026, recommandation de Claude sous la délégation du propriétaire) en `03b3a` (Rushing Out : hauteur de placement et sorties) et `03b3b` (Eccentricity : sorties inattendues, mécanisme à créer) : Eccentricity n'a aucun mécanisme existant (mémoire d'un « coup de tête » par action), l'ensemble dépassait le seuil de 2 h en confiance faible. Constat : Rushing Out est bien dans la base (50 gardiens notés de Ligue 1 : médiane 55, de 25 à 90 ; titulaires : de 30 à 90), contrairement à la phrase ci-dessus.

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 25 min |
| Développement | 40 min |
| Tests | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible (Eccentricity sans mécanisme existant). Temps machine, non compté : suite complète ; 50 matchs appariés.

## Acceptance criteria

- [ ] Constantes proposées au propriétaire avant le code
- [ ] Rushing Out élevé : position moyenne plus haute, plus de ballons interceptés derrière la défense (lob mesuré au `10b`)
- [ ] Eccentricity : plus de sorties inattendues, sans changer le niveau moyen
- [ ] Test de rayon et carte à jour
- [ ] Durée réelle relevée ; déterminisme ; suite V2 verte ; V1 inchangée
