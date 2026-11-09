# 05g: Validation des tirs : trajectoire, cadrage, contres, arrêts

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (contrôle des mécanismes avant toute calibration (22c)). **Catégorie :** validation.

**Constat vérifié :** le banc rapporte les issues du tir (28b) mais pas leur cohérence avec la distance, l'angle ou le tireur.

**What to build:** Rapport sur 50 matchs : issues par tranche de distance et d'angle, cadrés par tranche de Finishing / Long Shots, contrés selon le nombre de défenseurs dans le cône, taux d'arrêt selon la vitesse. Scènes de référence rejouées. Aucun réglage pour viser 8-15 tirs ou 10-11 % de conversion (repères vérifiés au 01c, réglage au 22c).

**Attributs :** aucun

**Blocked by:** 05a (Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ); 05b (Arrêt : le gardien atteint ou non le ballon); 05c (Contre : le défenseur touche réellement le tir); 05d (Déviation du ballon au contact d'un corps); 05e (La valeur du tir dans la décision suit la résolution physique); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée); 05h (Allumer le tir physique, découpé du 05b le 08/11/2026).

**Bloque :** 18a, 18e.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : élevée. Hypothèses : lecture de la trace des tirs.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : conversion décroissante avec la distance, cadrage croissant avec la note

## Acceptance criteria

- [ ] Rapport publié dans `docs/INDICATEURS_V2.md`
- [ ] Tendances attendues vérifiées (distance, note, contreurs) ; écarts au réel listés sans réglage
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Reprises du 05d (réserves de l'expert, 09/11/2026)

- **A2** : corners par match 8,6 → 6,6 avec la déviation physique des contres (repère réel environ 10) : mesurer la part des contres qui sortent derrière la ligne et en touche, et en traiter la cause (hauteur, orientation du corps) avant tout recalage compensatoire.
- **A1** : dans `match._blocked`, prendre la position du défenseur à l'instant du contact (`player.position − player.velocity·dt·(1 − entry)`) pour le point de contact et `deflect` ; test : défenseur qui traverse l'axe à 5 m/s, côté de la déviation celui du décalage au contact. À faire avant que la parade ou le contrôle raté n'adoptent `deflect`.
