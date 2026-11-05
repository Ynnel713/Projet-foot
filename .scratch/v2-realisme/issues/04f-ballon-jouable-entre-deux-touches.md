# 04f: Ballon jouable par un adversaire entre deux touches

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (la touche trop longue est l'erreur la plus courante en conduite). **Catégorie :** exécution.

**Constat vérifié :** voir 04e : sans ballon séparé du porteur, aucun adversaire ne peut le toucher pendant une conduite hors tacle.

**What to build:** Entre deux touches, le ballon peut être touché par un adversaire qui l'atteint avant le porteur (même détection de contact que les passes, `match._contacts`) ; la perte de conduite du 04a est alors en partie remplacée par ce mécanisme physique, sans double comptage (le tirage du 04a ne vaut plus que pour la dépossession au contact).

**Attributs :** aucun

**Blocked by:** 04e (Le ballon n'est plus collé au porteur).

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** ne pas cumuler le tirage du 04a et l'interception physique.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : faible. Hypothèses : réglage de la répartition entre tirage et physique à proposer.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur sur la trajectoire de la touche : il récupère le ballon
- **Statistiques (séries de matchs) :** 50 matchs : la calibration du 04c reste sous 3 points

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Interceptions entre deux touches tracées
- [ ] Courbe de calibration du 04c toujours respectée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
