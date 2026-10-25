# 05: Calibration de fin de socle

**What to build:** recalibration UNIQUE une fois les tickets 01 à 04 et 06 du socle livrés (décision du propriétaire, 25/10/2026 : ne pas recalibrer après chaque ticket, chacun déplaçant l'équilibre). Reprend les critères reportés des tickets 01 et 04. Réglages possibles : poids de décision (`decision.py`), attrait des passes longues, et tout autre levier identifié par les mesures, chacun proposé avant d'être appliqué.

**Blocked by:** 02, 03 et 06 du socle (01 et 04 livrés).

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] Tirs par équipe 8-15, buts par match 2-3,5 (repris des tickets 01 et 04)
- [ ] Receveur visé : au moins 50 % des passes (repris du ticket 01 ; 36,1 % mesuré au ticket 04)
- [ ] Passes de plus de 32 m : ~47 % réussies et 10 à 19 % des passes (Opta ; 71 % et 0,8 % mesurés au ticket 04)
- [ ] Passes réussies toujours 70-90 % et passes perdues toujours au plus 25 % (acquis du ticket 04, à ne pas perdre)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, voir `docs/REVUE_ATTRIBUTS_V2.md`) validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
