# 04: Généralisation — lot "transition / pressing"

**What to build:** les gabarits `recuperation_haute`, `decalage_enroulee` et `percee_individuelle` reçoivent chacun une phase de construction compatible, même principe que les lots précédents.

**Blocked by:** 03 (lot "jeu collectif ouvert") — séquencé pour garder `templates.py` vert lot après lot, un seul lot à la fois sur ce fichier partagé.

**Status:** ready-for-agent

- [ ] Chacun des 3 gabarits de ce lot est précédé d'au moins un type de phase de construction tactiquement cohérent
- [ ] Continuité des positions (ballon + joueurs) vérifiée sur un échantillon couvrant les 3 gabarits
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Les gabarits hors de ce lot sont 100 % identiques clip à clip
- [ ] Propriétaire valide visuellement un échantillon représentatif des 3 gabarits

**Point à trancher avec le propriétaire avant de coder `percee_individuelle` :** ce gabarit est conçu comme une action solo ("percée individuelle") ; lui ajouter une phase de construction collective contredit potentiellement son nom/design (signalé dans `docs/gabarit_durations_inventory.md`). Ne pas trancher seul — demander au propriétaire si la phase de construction doit rester solo (ex. pressing individuel avant la percée) ou si le gabarit sort du périmètre de ce chantier.

**Note :** fichiers sous exception (`CLAUDE.md`) concernés selon ce qui est réellement touché — demander l'exception avant de coder.
