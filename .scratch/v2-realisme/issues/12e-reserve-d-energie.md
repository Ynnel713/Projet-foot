# 12e: Réserve d'énergie qui dépend de l'effort

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (la fatigue vient de ce qu'on a couru, pas seulement de la minute). **Catégorie :** physique.

**Constat vérifié :** `movement.stamina_factor` (`movement.py:60`) ne dépend que de la minute et de Stamina, pas des efforts fournis.

**What to build:** Chaque joueur a une réserve d'énergie qui baisse avec l'intensité de course et remonte au repos ; Stamina règle la taille de la réserve et la recharge ; la vitesse maximale baisse quand la réserve est basse (remplace la baisse par la minute).

**Attributs :** Stamina

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-collectif/12` : réserve d'énergie.

**Blocked by:** 12d (Intensité de course selon le rôle).

**Bloque :** 12f, 12g, 13b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : modèle simple à deux paramètres (réserve, recharge).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** joueur qui sprinte 60 s : vitesse maximale réduite ; après 60 s de marche : remontée partielle
- **Comportementaux (profils comparés) :** Stamina 99 contre 11 : baisse plus tardive

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Réserve tracée
- [ ] Baisse de la course intense en fin de match rapportée (repère 10-30 %)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
