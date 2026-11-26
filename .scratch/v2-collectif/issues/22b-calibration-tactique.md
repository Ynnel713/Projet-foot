# 22b: Calibration, lot 2 : tactique collective

**Découpé du ticket 22 le 04/11/2026** (audit de granularité). Bases de référence et réserves : `22-calibration-generale.md`, sections « À surveiller depuis le ticket 08 » et « depuis le ticket 10 ».

**What to build:** régler les constantes tactiques (bloc, pressing, transitions, combinaisons, hors-jeu) sur le moteur dont les volumes sont calés par le 22a. Chaque levier est proposé avant d'être appliqué.

**Attributs :** tous.

**Blocked by:** 22a ; `v2-realisme/20e` (ajouté le 10/11/2026, audit de la roadmap) ; `v2-realisme/25h`, `27c` (ajoutés le 14/11/2026) ; `v2-collectif/15d` (ajouté le 21/11/2026, audit de réalisme du propriétaire) ; `v2-realisme/10m` (morceaux `10m1`, `10m2`), `10n` (ajoutés le 26/11/2026, audit des transitions).

**Bloque :** 22c.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Indicateurs tactiques du ticket 01 dans leurs fourchettes
- [ ] C2 du ticket 14 (une passe sans gain suivie d'une passe qui fait avancer, 39 % visé contre 30 à 32 % mesurés) ; échelle de progression de la deuxième passe au-delà de 20 m (A2 du ticket 13)
- [ ] Réserves du ticket 10 : latence du repli, tirs de contre après récupération, hors-jeu (rouvrir si moins de 1,5 par match, seuil du propriétaire du 26/11/2026 qui remplace les 2 de la réserve A3 du ticket 10) et recul du bloc (mécanisme traité au `v2-realisme/10m` ; contrôle chiffré ici)
- [ ] Les volumes du 22a restent dans leurs fourchettes (contrôle de non-régression)
- [ ] Leviers et critères validés par le propriétaire avant le code
- [ ] Repris du ticket 22 : courbes partagées de `attributes` ; chiffres réels sourcés, ou « non trouvé »
- [ ] Série d'au moins 40 matchs avec dispersion rapportée ; suite V2 verte ; V1 inchangée
