# 03: Généralisation — lot "jeu collectif ouvert"

**What to build:** les gabarits `construction_placee`, `debordement_centre_tete`, `une_deux` et `profondeur_1v1` reçoivent chacun une phase de construction compatible avec leur style, sur le même principe validé par le ticket 02. L'utilisateur voit désormais une construction d'action avant le geste décisif sur ces 4 gabarits en plus du pilote.

**Blocked by:** 02 (POC — phase de construction chaînée au gabarit pilote).

**Status:** ready-for-agent

- [ ] Chacun des 4 gabarits de ce lot est précédé d'au moins un type de phase de construction tactiquement cohérent
- [ ] Continuité des positions (ballon + joueurs) vérifiée sur un échantillon couvrant les 4 gabarits
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Les gabarits hors de ce lot (pilote + non encore traités) sont 100 % identiques clip à clip
- [ ] Propriétaire valide visuellement un échantillon représentatif des 4 gabarits

**Note :** fichiers sous exception (`CLAUDE.md`) concernés selon ce qui est réellement touché — demander l'exception avant de coder.

**Exceptions constatées et validées par le propriétaire (22/10/2026)**, voir `docs/TRD_PRODUIT.md` NFR-P02 :
- Plafond : si la conclusion existante dépasse déjà 40 s à elle seule (arrêt/poteau), la construction n'ajoute aucune seconde — même exception que le ticket 02.
- Plancher : sur `debordement_centre_tete`/`profondeur_1v1`, un but sans passeur crédité laisse la phase de construction omise (pas d'adversaire inventé pour une action sans passeur réel) — ~4 % des clips mesurés sur ces 2 gabarits.
