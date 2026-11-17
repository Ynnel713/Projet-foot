# 11m: Contacts restants entre coéquipiers : près de la cible et cibles mobiles

**Chantier :** `v2-realisme` (constat du ticket 11k, 15/11/2026). **Priorité :** P1. **Catégorie :** déplacement.

**Constat vérifié :** série appariée de 50 matchs (11k, `docs/INDICATEURS_V2.md` section 47) : contacts francs entre coéquipiers 336,5 → **106,5 par match**, cible de 30 non atteinte. Diagnostic sur 30 min de jeu (11j, `11j-diag-avant.txt`, 39 contacts) : aucun à cibles confondues ; l'un des deux à moins de 2 m de sa propre cible dans 23 cas ; au moins une cible mobile (pressing, soutien) dans 19 ; paires de rôles les plus fréquentes : couverture + presseur, replacement + replacement, gardien + tenir sa place, presseur + replacement, marquage + presseur.

**What to build:** À cadrer avant le code, sur un diagnostic plus fin des 106,5 contacts (vitesse et phase de course de chacun, évitement actif ou non, qui percute qui). Pistes du 11f non tranchées : (a) freinage au-delà de 50 % (jusqu'à l'arrêt) quand la cible elle-même est dans le couloir du coéquipier ; (c) horizon plus long à haute vitesse ; et coupure de l'horizon au temps d'arrivée à la cible (réserve A2 du 11f). Chaque piste à proposer au propriétaire avec ses constantes.

**Attributs :** aucun a priori (règle R1 de l'évitement).

**Blocked by:** 11k (livré).

**Bloque :** rien.

**Status:** à faire (cadrage : diagnostic d'abord ; leçon du 11j, refaire le diagnostic sur le moteur courant avant de coder)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et diagnostic | 30 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : faible (piste non choisie). Au-delà de 2 h : à découper après le diagnostic (diagnostic seul, puis un ticket par piste retenue).
Temps machine, non compté : diagnostic de 30 min de jeu ; série appariée de 50 matchs ; suite complète.

## Acceptance criteria

- [ ] Diagnostic des contacts restants rapporté ; piste et constantes validées par le propriétaire avant le code
- [ ] Contacts francs entre coéquipiers : sous 30 par match (cible indicative du 11k, à reconfirmer)
- [ ] Sans régression significative (50 matchs appariés) sur buts, tirs, passes réussies, pressings, appels ; rythme rapporté
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
