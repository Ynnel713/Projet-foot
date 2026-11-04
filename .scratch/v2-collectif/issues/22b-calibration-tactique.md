# 22b: Calibration, lot 2 : tactique collective

**Découpé du ticket 22 le 04/11/2026** (audit de granularité). Bases de référence et réserves : `22-calibration-generale.md`, sections « À surveiller depuis le ticket 08 » et « depuis le ticket 10 ».

**What to build:** régler les constantes tactiques (bloc, pressing, transitions, combinaisons, hors-jeu) sur le moteur dont les volumes sont calés par le 22a. Chaque levier est proposé avant d'être appliqué.

**Attributs :** tous.

**Blocked by:** 22a.

**Bloque :** 22c.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Indicateurs tactiques du ticket 01 dans leurs fourchettes
- [ ] C2 du ticket 14 (une passe sans gain suivie d'une passe qui fait avancer, 39 % visé contre 30 à 32 % mesurés) ; échelle de progression de la deuxième passe au-delà de 20 m (A2 du ticket 13)
- [ ] Réserves du ticket 10 : latence du repli, tirs de contre après récupération, hors-jeu (rouvrir si moins de 2 par match) et recul du bloc
- [ ] Les volumes du 22a restent dans leurs fourchettes (contrôle de non-régression)
- [ ] Leviers et critères validés par le propriétaire avant le code
- [ ] Repris du ticket 22 : courbes partagées de `attributes` ; chiffres réels sourcés, ou « non trouvé »
- [ ] Série d'au moins 40 matchs avec dispersion rapportée ; suite V2 verte ; V1 inchangée
