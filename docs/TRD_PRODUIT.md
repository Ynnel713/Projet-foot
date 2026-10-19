# TRD — Simulafoot (construction multi-phases des temps forts)

> Traduit techniquement les User Stories 13 à 16 de `docs/PRD_PRODUIT.md`. Ne duplique pas l'architecture d'ensemble déjà couverte par `docs/TRD_SIMULAFOOT.pdf` (v1.1) et `docs/TRD_MAJ.md` (changelog jusqu'à v1.9) — s'y réfère sans la recopier.

## Contexte technique

Simulafoot est un projet personnel en production active, avec un TRD existant volumineux (`docs/TRD_SIMULAFOOT.pdf` v1.1, complété par `docs/TRD_MAJ.md` jusqu'à v1.9) couvrant déjà l'architecture d'ensemble (moteur Poisson, API FastAPI, PWA React, pipeline graphique, NLG). Ce document ne la duplique pas : il traduit techniquement les user stories 13 à 16 du nouveau cadrage produit (`docs/PRD_PRODUIT.md`) — la construction multi-phases des temps forts animés — qui n'a pas encore d'ancrage technique.

## Architecture & composants

**Pipeline actuel (rappel, inchangé) :** `narrative.py` (timeline d'événements déjà décidés) → `templates.py` (12 gabarits, chacun un seul geste décisif) → `sequence_generator.py`/`ball.py`/`motion.py` (positions et physique) → `narrative_player.py` (clips 30 im/s) → API `/animation` → `canvas.html`.

**Nouveau mécanisme : séquence composite.**
- Un temps fort n'est plus un gabarit unique mais l'enchaînement déterministe de 1 à 3 « phases de construction » (nouveaux gabarits courts, sans geste décisif : perte de balle, transition, pressing, faute...) suivies d'une « phase de conclusion » correspondant à l'un des 12 gabarits existants, inchangés en tant que tels. (US-13)
- Chaque phase démarre exactement là où la précédente s'est arrêtée (continuité des positions des joueurs scriptés, des joueurs de décor, et du ballon) — aucun saut visible à la jonction entre deux phases.
- Le nombre de phases et leur durée sont tirés déterministiquement (sha256 de `event_ref`, même mécanisme que le reste du rendu) en ignorant strictement si l'événement se conclut par un but — garantit l'absence de corrélation durée/issue. (US-14)
- La durée totale d'un temps fort tombe dans [10, 40] secondes, jamais sous 10 secondes.
- Aucune phase de construction n'introduit de nouvel aléa sportif : le moteur Poisson et `events.py` restent inchangés (décision D-001 ci-dessous).

**Contrat API `/animation` et barre de progression.**
- La barre de progression (`canvas.html`) n'affiche un marqueur de temps fort qu'une fois ce temps fort atteint pendant la lecture (décision D-002).
- Recommandation : le payload réseau reste transmis en une fois comme aujourd'hui (cohérent avec le contrat existant) ; la dissimulation des temps forts à venir est traitée uniquement côté front, pas par un changement du contrat API (décision D-003, à valider).

## Données & modèle

Aucune nouvelle source de données externe. Les phases de construction forment un catalogue de gabarits supplémentaire, défini en code (même mécanisme que les 12 gabarits existants dans `templates.py`) — pas une nouvelle donnée persistée.

## Sécurité & confidentialité

Inchangé (voir TRD existant, ENF-FIA/ENF-SEC). Rien dans ce chantier n'ajoute de surface d'attaque, de donnée personnelle ou d'accès réseau.

## Performance & fiabilité

- **NFR-P01** — Sur un échantillon de temps forts, la durée n'est pas statistiquement corrélée à l'issue (but ou non).
- **NFR-P02** — Chaque temps fort dure entre 10 et 40 secondes ; 0 clip hors bornes sur l'échantillon de référence.
- **NFR-P03** — À la jonction entre deux phases, aucun joueur (scripté ou décor) ne présente un saut de position supérieur à la tolérance déjà en vigueur ailleurs dans le rendu.
- **NFR-P04** — L'animation d'un match s'ouvre en moins de 10 secondes au premier chargement, y compris avec des temps forts multi-phases plus longs à construire (repris du PRD).
- **NFR-P05** — Déterminisme bit-à-bit conservé (même graine = mêmes positions, mêmes durées, mêmes choix de phases).

## Stratégie de tests

- **TEST-01** — Plancher de durée (10 s) respecté par construction, quel que soit le nombre de phases tirées.
- **TEST-02** — Absence de corrélation mesurée entre durée totale d'un temps fort et son issue, sur pipeline réel.
- **TEST-03** — Continuité aux jonctions de phases (ballon + joueurs), sur un échantillon de temps forts multi-phases.
- **TEST-04** — Déterminisme bit-à-bit sur des temps forts multi-phases.
- **TEST-05** — Non-régression du résultat sportif (score, buteurs, cartons, remplacements strictement identiques avant/après).
- **TEST-06** — La barre de progression ne révèle aucun marqueur de temps fort non encore atteint pendant la lecture.

## Décisions techniques

- **D-001** — Construction multi-phases : habillage narratif pur, aucun nouvel événement réel dans le moteur. **Validé.**
- **D-002** — Barre de progression : marqueurs masqués jusqu'à visionnage. **Validé.**
- **D-003** — Contrat API `/animation` inchangé ; dissimulation traitée côté front uniquement. **Recommandé, à valider.**
- **D-004** — Bibliothèque de phases de construction : un petit catalogue fixe (de l'ordre de 4 à 6 types réutilisables), combiné déterministiquement avec les 12 gabarits de conclusion existants, plutôt qu'une génération libre illimitée. **Recommandé, à valider.**

## Hors périmètre technique

- Toute modification du moteur Poisson (`events.py`, `simulation.py`).
- La persistance de l'état d'une compétition (hors périmètre du PRD).
- Le détail de chaque phase gabarit par gabarit (positions, durées précises) — relève du plan d'implémentation (`/planifie`), pas de ce TRD.
- L'articulation fine avec le chantier « mouvement collectif » en cours : ce TRD suppose sa clôture avant que la construction multi-phases démarre.

## Notes complémentaires

- Risque technique majeur : `templates.py`, `narrative.py`, `sequence_generator.py`, `ball.py`/`motion.py` sont tous sous exception explicite requise par `CLAUDE.md` — toute implémentation nécessitera de demander ces exceptions avant de coder.
- Dépendance d'ordre : ce chantier suppose probablement la clôture du chantier « mouvement collectif » (Phase 5 en attente) et d'A1.1 (inertie), pour ne pas cumuler deux refontes de `motion.py`/`templates.py` en parallèle — à confirmer avec `simulafoot-architect` au moment de planifier.
- D-003 et D-004 sont des recommandations de cadrage, pas des constantes déjà validées — à reproposer individuellement avant implémentation, comme toute constante produit.
