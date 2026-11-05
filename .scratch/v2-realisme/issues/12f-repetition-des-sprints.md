# 12f: Répéter les sprints et récupérer

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (la capacité à enchaîner les efforts différencie les profils). **Catégorie :** physique.

**Constat vérifié :** aucune notion de sprint répété : un joueur peut sprinter sans fin (vitesse maximale bornée seulement par la minute).

**What to build:** Une composante rapide de la réserve (anaérobie) se vide pendant un sprint et se recharge en quelques dizaines de secondes ; vide, le joueur ne peut plus sprinter (intensité plafonnée). Natural Fitness reste hors du match (D-V10) ; Stamina règle la recharge.

**Attributs :** Stamina (recharge)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-collectif/12` : répétition des efforts.

**Blocked by:** 12e (Réserve d'énergie qui dépend de l'effort).

**Bloque :** 12g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : constantes de recharge à sourcer.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** 5 sprints de 30 m espacés de 10 s : vitesse décroissante ; espacés de 60 s : stable

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de répétition mesuré en scène
- [ ] Sprints par match rapportés
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
