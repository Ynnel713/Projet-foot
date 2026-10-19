# Plan : Construction multi-phases des temps forts

> PRD source : `docs/PRD_PRODUIT.md` (US-13 à 16) · TRD source : `docs/TRD_PRODUIT.md` (D-001 à D-004)

## Décisions architecturales

- **Mécanisme** : chaque temps fort devient une séquence de 1 à 3 « phases de construction » (nouveaux gabarits courts, sans geste décisif : perte de balle, transition, pressing, faute...) suivies d'une « phase de conclusion » correspondant à l'un des 12 gabarits existants, inchangés en tant que tels. Jamais 0 phase de construction — garantit le plancher de 10 secondes sur tous les temps forts, pas seulement les buts.
- **Catalogue de phases** : ensemble fixe (de l'ordre de 4 à 6 types réutilisables), pas de génération libre/combinatoire illimitée (D-004).
- **Tirage déterministe** : sha256 de `event_ref` pour le nombre de phases et leur durée, même mécanisme que le reste du rendu ; ignore strictement si l'événement se conclut par un but ou non (D-001).
- **Moteur sportif** : le moteur Poisson et `events.py` ne sont jamais modifiés ; aucune phase de construction n'introduit de nouvel aléa sportif (D-001).
- **Front / API** : la barre de progression (`canvas.html`) ne révèle un marqueur de temps fort qu'une fois ce temps fort atteint pendant la lecture (D-002) ; le contrat API `/animation` reste inchangé, le payload continue d'être transmis en une fois (D-003).
- **Fichiers sous exception** : `templates.py`, `narrative.py`, `sequence_generator.py`, `ball.py`/`motion.py` et `render/canvas.html` sont tous sous exception explicite requise par `CLAUDE.md` — à demander au propriétaire avant de coder, phase par phase, selon les fichiers réellement touchés.
- **Préalable externe** : ce chantier dépend de la clôture du chantier « mouvement collectif » en cours (Phase 5 en attente de validation/commit) et d'A1.1 (inertie, codée, en attente de commit), pour ne pas cumuler deux refontes de `motion.py`/`templates.py` en parallèle. Ces deux chantiers sont pilotés ailleurs, hors de ce plan.

---

## Phase 1 : Masquage des temps forts à venir (barre de progression)

**User stories** : US-15, US-16

### Ce qu'on livre

La barre de progression du lecteur (`canvas.html`) n'affiche plus tous les marqueurs de temps forts d'un coup au chargement d'un match. Chaque marqueur n'apparaît qu'au moment où son temps fort est atteint pendant la lecture ; un temps fort déjà visionné garde son marqueur visible (navigation arrière possible). Ne touche ni au moteur, ni à la narration, ni au contrat réseau — uniquement à l'affichage côté lecteur.

### Critères d'acceptation

- [ ] Au lancement d'un match, aucun marqueur n'est visible au-delà du temps fort en cours ou déjà passé
- [ ] Un marqueur apparaît exactement quand son temps fort commence à être lu
- [ ] Revenir en arrière sur un temps fort déjà vu reste possible, son marqueur reste visible
- [ ] Aucune régression sur le reste du lecteur (lecture, pause, enchaînement de clips)
- [ ] Propriétaire valide qu'il ne peut pas deviner, en début de match, combien de temps forts il reste à voir

## Bloquée par

- Aucune — démarrable immédiatement.

---

## Phase 2 : Preuve de concept — une phase de construction chaînée à un gabarit pilote

**User stories** : US-13 (cas pilote)

### Ce qu'on livre

Un unique type de phase de construction (par exemple « perte de balle / transition ») précède un seul gabarit de conclusion existant choisi comme pilote, pour les temps forts qui l'utilisent. Le ballon et les joueurs (scriptés et décor) repartent exactement de la position où la phase de construction s'est arrêtée, sans saut visible à la jonction. Visible dans la vraie PWA pour ce gabarit uniquement ; les 11 autres gabarits restent inchangés (un seul geste décisif, comme aujourd'hui).

### Critères d'acceptation

- [ ] Sur l'échantillon de référence, les clips du gabarit pilote durent au moins 10 secondes
- [ ] Aucun saut de position mesurable à la jonction entre la phase de construction et la conclusion
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif (score, buteurs, cartons, remplacements) strictement identique
- [ ] Les 11 autres gabarits sont 100 % identiques clip à clip (aucun effet de bord)
- [ ] Propriétaire valide visuellement la continuité sur un échantillon de clips du gabarit pilote

## Bloquée par

- Clôture du chantier « mouvement collectif » (Phase 5) et d'A1.1 — pilotés ailleurs, hors de ce plan.

---

## Phase 3 : Généralisation du catalogue de phases aux 12 gabarits de conclusion

**User stories** : US-13 (complet)

### Ce qu'on livre

Le catalogue complet de phases de construction (D-004, de l'ordre de 4 à 6 types) devient combinable avec l'ensemble des 12 gabarits de conclusion existants, pas seulement le pilote de la Phase 2. Chaque gabarit de conclusion est précédé d'au moins un type de phase de construction tactiquement cohérent avec lui.

### Critères d'acceptation

- [ ] Chaque gabarit de conclusion peut être précédé d'au moins un type de phase de construction compatible
- [ ] Continuité des positions (ballon + joueurs) vérifiée sur un échantillon couvrant les 12 gabarits
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Propriétaire valide visuellement un échantillon représentatif des 12 gabarits

## Bloquée par

- Phase 2

---

## Phase 4 : Tirage déterministe de la durée (10-40s), décorrélé de l'issue

**User stories** : US-14

### Ce qu'on livre

Le nombre de phases de construction (1 à 3) et la durée totale d'un temps fort sont tirés déterministiquement, avec un plancher strict de 10 secondes et un plafond de 40 secondes, sans aucune dépendance au fait que l'événement se conclue par un but ou non.

### Critères d'acceptation

- [ ] 0 clip sous 10 secondes et 0 clip au-dessus de 40 secondes sur l'échantillon de référence
- [ ] Sur l'échantillon, aucune corrélation statistique mesurable entre durée et issue (but / non-but)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Propriétaire valide, sur un échantillon de clips mélangés, qu'il ne peut pas deviner l'issue à partir de la durée

## Bloquée par

- Phase 3
