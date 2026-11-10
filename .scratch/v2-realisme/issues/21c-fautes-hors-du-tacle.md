# 21c: Fautes hors du tacle : tirage de maillot, charge, faute tactique

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (le volume de fautes manque d'un mécanisme, il ne doit pas se combler par un réglage). **Catégorie :** arbitrage.

**Constat vérifié :** seules les tentatives de tacle produisent des fautes (`duel.py`) : 9,4 fautes par match contre 21 à 26 en réel (ticket `v2-collectif/30`, écart renvoyé au 22a). Règle des calibrations : un écart dû à un mécanisme absent devient un ticket.

**What to build:** Trois sources nouvelles : contact irrégulier au duel d'épaule (11c) ou à la protection du ballon (04i) ; tirage de maillot du défenseur battu (après un contournement 04g ou un appel dans son dos) ; faute tactique volontaire pour casser une transition (choix du joueur, Decisions ; gravité 21b).

**Attributs :** Decisions (choisir la faute tactique) ; Aggression inchangée (fréquence des contacts).

**Blocked by:** 11c, 04g, 04i, 21b.

**Bloque :** `v2-collectif/22a` (volume des fautes).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : chaque source réutilise une situation déjà détectée par le moteur.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur battu sur un contournement : tirage de maillot possible, plus fréquent si la transition est dangereuse
- **Statistiques (séries de matchs) :** 50 matchs : fautes par match par source

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Trois sources tracées
- [ ] Fautes par match rapportées (aucun réglage pour viser 21-26)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
