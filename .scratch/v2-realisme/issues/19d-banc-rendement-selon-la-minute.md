# 19d: Banc : rendement selon la minute et la fatigue (état des lieux)

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P0 (avant 18a : mesurer ce que la fatigue change aujourd'hui avant de construire 12d, 12e et 20). **Catégorie :** mesure.

**Constat vérifié :** la fatigue ne dépend que de la minute et de Stamina, et n'agit que sur la vitesse maximale (`movement.stamina_factor`, `movement.py:60`) ; aucun indicateur du banc ne découpe le match par tranche de temps.

**What to build:** Indicateurs par tranche de 15 minutes, par joueur et par poste : distance, distance au-dessus de 19,8 et 25 km/h, sprints, réussite des passes et des contrôles, cadrage, duels gagnés, hauteur du bloc, buts marqués et encaissés. Comparaison de la première et de la dernière tranche par note de Stamina. Scène A/B : même joueur à la 15e et à la 85e. Section nouvelle de `docs/INDICATEURS_V2.md`. Lecture seule.

**Attributs :** aucun

**Blocked by:** 01d, 01e (livrés).

**Bloque :** 18a ; 20d.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : élevée. Hypothèses : lecture de la trace et de l'observateur existant.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : profil par tranche publié ; hypothèse à vérifier : seules les grandeurs de course baissent, la technique et les décisions sont plates

## Acceptance criteria

- [ ] Section publiée dans `docs/INDICATEURS_V2.md`
- [ ] Constat chiffré sur ce que la fatigue change et ne change pas
- [ ] Jeu inchangé
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
