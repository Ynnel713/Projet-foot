# 03d: Gardien : sortie sur un ballon dans la profondeur

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (une passe en profondeur doit pouvoir être coupée par le gardien). **Catégorie :** décision.

**Constat vérifié :** le gardien ne court au ballon libre que s'il est le plus proche de son équipe ou à moins de 15 m (règle générale `BALLON_LIBRE`) ; aucune comparaison avec l'attaquant ni limite de surface.

**What to build:** Sur une passe adverse ou un ballon libre vers son but, le gardien compare son temps d'arrivée à celui de l'attaquant le plus rapide (même calcul que `defense.arrival_time_s`) ; s'il arrive avant avec une marge validée, il sort (état « sortie ») ; sinon il reste en placement. Hors de sa surface, il dégage ou joue au pied, jamais à la main.

**Hors de ce ticket :** le ticket `v2-attributs-restants/03b` ajoutera les tendances et notes du gardien (Rushing Out, Eccentricity, One on Ones…) sur ces mécanismes neutres ; aucun attribut de gardien ici.

**Attributs :** aucun

**Blocked by:** 03c (Gardien : hauteur selon le ballon et la ligne défensive (couverture de la profondeur)).

**Bloque :** 03g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : le jeu à la main hors surface n'existe pas aujourd'hui ; le dégagement réutilise la passe existante.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** passe en profondeur, gardien à 20 m du point de chute, attaquant à 30 m : il sort ; attaquant à 10 m : il reste
- **Statistiques (séries de matchs) :** 50 matchs : sorties par match et part réussie

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Décision de sortir fondée sur les temps d'arrivée, tracée
- [ ] Aucune prise à la main hors de la surface (test)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
