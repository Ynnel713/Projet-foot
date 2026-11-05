# 12d: Intensité de course selon le rôle

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (tout le monde ne sprinte pas : trot, course, sprint selon ce qu'il fait). **Catégorie :** physique.

**Constat vérifié :** hors presseur et repli (Work Rate, tickets 08 et 10), remises en jeu et réception, les intentions visent l'intensité 1,0, c'est-à-dire la vitesse maximale (`cerveau.Intention.intensity`) ; mesure de référence : 37 % du temps au-dessus de 19,8 km/h (26/10/2026) contre 2-5 % au réel.

**What to build:** Chaque rôle a une intensité de base (tenir sa place : trot ; replacement : course ; appel dans la profondeur, presseur, repli urgent : sprint) ; l'attribut mental qui gouverne le rôle module (Work Rate sans ballon, Off the Ball pour les appels) sans recompter les effets déjà branchés.

**Attributs :** Work Rate, Off the Ball (rayons existants)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-collectif/12` : intensité par rôle.

**Blocked by:** 02f (Tenir sa position en possession).

**Bloque :** 12e, 12g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : intensités de base proposées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** joueur qui tient sa place loin du ballon : vitesse sous le seuil de trot
- **Statistiques (séries de matchs) :** 50 matchs : temps au-dessus de 19,8 km/h, km par joueur

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Intensité par rôle documentée et tracée
- [ ] Temps à haute intensité en baisse mesurée
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
