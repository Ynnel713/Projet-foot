# Plan : Construction multi-phases des temps forts

> PRD source : `docs/PRD_PRODUIT.md` (US-13 à 16) · TRD source : `docs/TRD_PRODUIT.md` (D-001 à D-004)

## Décisions architecturales

- **Mécanisme** : chaque temps fort devient une séquence de 1 à 3 « phases de construction » (nouveaux gabarits courts, sans geste décisif : perte de balle, transition, pressing, faute...) suivies d'une « phase de conclusion » correspondant à l'un des 12 gabarits existants, inchangés en tant que tels. Jamais 0 phase de construction — garantit le plancher de 20 secondes sur tous les temps forts, pas seulement les buts.
- **Catalogue de phases** : ensemble fixe de l'ordre de 8 à 12 types réutilisables (validé 22/10/2026, D-004) — par exemple possession adverse, perte de balle/tacle, interception, pressing, faute, transition, récupération haute... — pas de génération libre/combinatoire illimitée.
- **Tirage déterministe** : sha256 de `event_ref` pour le nombre de phases et leur durée, même mécanisme que le reste du rendu ; ignore strictement si l'événement se conclut par un but ou non (D-001).
- **Moteur sportif** : le moteur Poisson et `events.py` ne sont jamais modifiés ; aucune phase de construction n'introduit de nouvel aléa sportif (D-001).
- **Front / API** : la barre de progression (`canvas.html`) ne révèle un marqueur de temps fort qu'une fois ce temps fort atteint pendant la lecture (D-002) ; le contrat API `/animation` reste inchangé, le payload continue d'être transmis en une fois (D-003).
- **Fichiers sous exception** : `templates.py`, `narrative.py`, `sequence_generator.py`, `ball.py`/`motion.py` et `render/canvas.html` sont tous sous exception explicite requise par `CLAUDE.md` — à demander au propriétaire avant de coder, phase par phase, selon les fichiers réellement touchés.
- **Préalable externe** : ce chantier dépend de la clôture du chantier « mouvement collectif » en cours (Phase 5 en attente de validation/commit) et d'A1.1 (inertie, codée, en attente de commit), pour ne pas cumuler deux refontes de `motion.py`/`templates.py` en parallèle. Ces deux chantiers sont pilotés ailleurs, hors de ce plan.

---

## Phase 1 : Masquage des temps forts à venir (barre de progression)

**Statut** : Implémentée, validée QC (`/valider-etape`, sous-étape `temps-forts-multiphases-01`, 22/10/2026) — en attente de la validation visuelle du propriétaire (dernier critère ci-dessous). Un défaut supplémentaire trouvé en revue (le compteur `Clip N / Total` révélait le total dès le premier clip) a été corrigé dans le même ticket.

**User stories** : US-15, US-16

### Ce qu'on livre

La barre de progression du lecteur (`canvas.html`) n'affiche plus tous les marqueurs de temps forts d'un coup au chargement d'un match. Chaque marqueur n'apparaît qu'au moment où son temps fort est atteint pendant la lecture ; un temps fort déjà visionné garde son marqueur visible (navigation arrière possible). Ne touche ni au moteur, ni à la narration, ni au contrat réseau — uniquement à l'affichage côté lecteur.

### Critères d'acceptation

- [x] Au lancement d'un match, aucun marqueur n'est visible au-delà du temps fort en cours ou déjà passé
- [x] Un marqueur apparaît exactement quand son temps fort commence à être lu
- [x] Revenir en arrière sur un temps fort déjà vu reste possible, son marqueur reste visible
- [x] Aucune régression sur le reste du lecteur (lecture, pause, enchaînement de clips)
- [ ] Propriétaire valide qu'il ne peut pas deviner, en début de match, combien de temps forts il reste à voir

## Bloquée par

- Aucune — démarrable immédiatement.

---

## Phase 2 : Preuve de concept — une phase de construction chaînée à un gabarit pilote

**User stories** : US-13 (cas pilote)

**Statut** : Implémentée, validée QC (`/valider-etape`, sous-étape `temps-forts-multiphases-02`, 22/10/2026) — en attente de la validation visuelle du propriétaire (dernier critère ci-dessous).

**Gabarit pilote confirmé (22/10/2026)** : `contre_attaque`. Scénario donné par le propriétaire : possession adverse → perte de balle (tacle, passe interceptée, ou autre) → contre-attaque (conclusion existante, inchangée). Deux phases de construction enchaînées (possession adverse, puis perte de balle/turnover) avant la conclusion.

### Ce qu'on livre

Les phases de construction « possession adverse » et « perte de balle » précèdent le gabarit de conclusion `contre_attaque`, pour les temps forts qui l'utilisent. Le ballon et les joueurs (scriptés et décor) repartent exactement de la position où chaque phase s'est arrêtée, sans saut visible aux jonctions. Visible dans la vraie PWA pour ce gabarit uniquement ; les 11 autres gabarits restent inchangés (un seul geste décisif, comme aujourd'hui).

### Critères d'acceptation

- [x] Sur l'échantillon de référence, les clips du gabarit pilote durent au moins 20 secondes
- [x] Aucun saut de position mesurable à la jonction entre la phase de construction et la conclusion
- [x] Déterminisme bit-à-bit vérifié
- [x] Résultat sportif (score, buteurs, cartons, remplacements) strictement identique
- [x] Les 11 autres gabarits sont 100 % identiques clip à clip (aucun effet de bord)
- [ ] Propriétaire valide visuellement la continuité sur un échantillon de clips du gabarit pilote

## Bloquée par

- Clôture du chantier « mouvement collectif » (Phase 5) et d'A1.1 — pilotés ailleurs, hors de ce plan.

---

## Phase 3 : Généralisation du catalogue de phases aux 12 gabarits de conclusion

**User stories** : US-13 (complet)

**Statut** : Lots 1/3, 2/3 et 3/3 livrés — les 12 gabarits sur 12 ont une phase de construction. Lot 3 — ticket 05 (`but_gag` sur le mécanisme commun ; `coup_franc`/`penalty` : la faute qui a provoqué le coup de pied arrêté, un seul adversaire fautif replacé ensuite à distance réglementaire ; `corner` : dégagement contré par un seul défenseur), validé QC (sous-étape `temps-forts-multiphases-05`, 23/10/2026, après un premier verdict BLOQUÉ levé). Au passage, les coéquipiers du tireur de penalty sont désormais hors de l'arc (décision du propriétaire). Reste au propriétaire : validation visuelle d'un échantillon des 12 gabarits. Lot 1 — ticket 03 (`construction_placee`, `debordement_centre_tete`, `une_deux`, `profondeur_1v1`), validé QC (sous-étape `temps-forts-multiphases-03`, 22/10/2026). Lot 2 — ticket 04 (`recuperation_haute`, `decalage_enroulee`, `percee_individuelle`, y compris ce dernier malgré son nom "solo" : la construction décrit la perte de balle ADVERSE, jamais le côté collectif/solo de la conclusion), validé QC (sous-étape `temps-forts-multiphases-04`, 22/10/2026). Un seul type de phase réutilisé pour ces 8 gabarits (pas de catalogue de types tiré par gabarit, tranché avec le propriétaire le 22/10/2026 : le nom de "type" n'est jamais affiché par le rendu, la variété géographique suffit). Exception plancher constatée (TRD NFR-P02) : un but sans passeur crédité laisse `debordement_centre_tete`/`profondeur_1v1`/`decalage_enroulee` sans phase de construction (~4-5 % des clips mesurés). **Défaut visuel signalé par le propriétaire en test live (22/10/2026)** : les deux adversaires scriptés (et le(s) rôle(s) actif(s) du camp qui marque) étaient figés pendant toute la construction (choix délibéré du ticket 02) — corrigé par le ticket 07 (léger balancement borné) avant le lot 2, pour ne pas répandre le défaut à 3 gabarits de plus.

### Ce qu'on livre

Le catalogue complet de phases de construction (D-004, de l'ordre de 8 à 12 types) devient combinable avec l'ensemble des 12 gabarits de conclusion existants, pas seulement le pilote de la Phase 2. Chaque gabarit de conclusion est précédé d'au moins un type de phase de construction tactiquement cohérent avec lui.

### Critères d'acceptation

- [ ] Chaque gabarit de conclusion peut être précédé d'au moins un type de phase de construction compatible
- [ ] Continuité des positions (ballon + joueurs) vérifiée sur un échantillon couvrant les 12 gabarits
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Propriétaire valide visuellement un échantillon représentatif des 12 gabarits

## Bloquée par

- Phase 2

---

## Phase 4 : Tirage déterministe de la durée (20-40s), décorrélé de l'issue

**User stories** : US-14

**Statut** : Livrée, validée QC (sous-étape `temps-forts-multiphases-06`, 23/10/2026). Durée FINALE du clip (suite du tir comprise) identique pour toutes les issues d'une même action ; 0 clip hors [20, 40[ s sur l'échantillon de référence (contre 22 sous 20 s et 92 à 40 s ou plus avant). Résidu de corrélation accepté par le propriétaire (AUC 0,549, détectable seulement sur `debordement_centre_tete`, voir TRD NFR-P01). « Nombre de phases 1 à 3 » sorti de cette phase (variété visuelle, non planifié). Reste : validation visuelle du propriétaire.

### Ce qu'on livre

Le nombre de phases de construction (1 à 3) et la durée totale d'un temps fort sont tirés déterministiquement, avec un plancher strict de 20 secondes et un plafond de 40 secondes sur la durée AJOUTÉE par la construction, sans aucune dépendance au fait que l'événement se conclue par un but ou non. **Exception validée par le propriétaire (22/10/2026)** : si la conclusion existante (inchangée) dépasse déjà 40 secondes à elle seule (cas mesuré, ~6,6 % des clips `contre_attaque` réels, issues « arrêt »/« poteau »), la construction n'ajoute aucune seconde et la durée totale dépasse 40 secondes en conséquence — la conclusion n'est jamais raccourcie pour tenir ce plafond.

### Critères d'acceptation

- [ ] 0 clip sous 20 secondes ; 0 clip au-dessus de 40 secondes sur l'échantillon de référence, sauf les clips dont la conclusion seule dépasse déjà 40 secondes (exception validée ci-dessus)
- [ ] Sur l'échantillon, aucune corrélation statistique mesurable entre durée et issue (but / non-but)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Propriétaire valide, sur un échantillon de clips mélangés, qu'il ne peut pas deviner l'issue à partir de la durée

## Bloquée par

- Phase 3

## Chantier mis en pause après cette phase (23/10/2026)

**Décision du propriétaire (interview `/grill-me`, session forkée, 23/10/2026)** : le rendu animé reste peu cohérent sur la majorité des joueurs (mouvement en bloc/générique hors rôle scripté actif, cf. `docs/known_issues.md` et `docs/PRD_PRODUIT.md` US-19) — priorité donnée à corriger ce problème de fond avant de poursuivre la richesse narrative. Une fois la Phase 4 ci-dessus terminée et validée, ce chantier (`temps-forts-multiphases`) s'arrête ici (le travail déjà livré, phases 1 à 4, reste en place) ; la session principale bascule sur `.scratch/plafond-vitesse-partage/01` puis `.scratch/mouvement-riche-tous-joueurs/01` à `/09`. Aucune reprise de ce chantier n'est planifiée pour l'instant.
