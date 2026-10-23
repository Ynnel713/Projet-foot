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
- La durée totale d'un temps fort tombe dans [20, 40] secondes, jamais sous 20 secondes. **Exception plafond validée par le propriétaire (22/10/2026)** : si la phase de conclusion existante (inchangée par ce chantier) dépasse déjà 40 secondes à elle seule — mesuré sur ~6,6 % des clips `contre_attaque` réels, issues « arrêt »/« poteau » —, la phase de construction n'ajoute alors aucune seconde supplémentaire (durée ajoutée = 0) et la durée totale dépasse 40 secondes en conséquence. Seule la durée AJOUTÉE par la construction est plafonnée à 40 secondes moins la durée de la conclusion ; la conclusion existante n'est jamais raccourcie pour tenir ce plafond. **Exception plancher validée par le propriétaire (22/10/2026, ticket 03, étendue au ticket 04)** : pour les gabarits dont le point d'ancrage de la phase de construction est le passeur (`debordement_centre_tete`, `profondeur_1v1`, `decalage_enroulee`), un but marqué sans passe décisive créditée (`event.assist is None`, dette connue du 23/09/2026) laisse ce rôle non résolu — la phase de construction est alors omise (repli neutre, pas d'adversaire inventé pour une action qui n'a jamais eu de passeur) et le clip garde sa durée d'origine, sous 20 secondes (~4-5 % des clips mesurés sur ces 3 gabarits). Inventer un adversaire fictif pour forcer le plancher serait moins honnête qu'omettre la construction sur ce cas précis.
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
- **NFR-P02** — Chaque temps fort dure entre 20 et 40 secondes ; 0 clip hors bornes sur l'échantillon de référence, sauf (a) si la conclusion existante (inchangée) dépasse déjà 40 s à elle seule, auquel cas la durée ajoutée par la construction est 0 et la durée totale égale celle de la conclusion seule, ou (b) sur `debordement_centre_tete`/`profondeur_1v1`/`decalage_enroulee`, si le but n'a pas de passeur crédité (voir exceptions validées ci-dessus).
- **NFR-P03** — À la jonction entre deux phases, aucun joueur (scripté ou décor) ne présente un saut de position supérieur à la tolérance déjà en vigueur ailleurs dans le rendu.
- **NFR-P04** — L'animation d'un match s'ouvre en moins de 10 secondes au premier chargement, y compris avec des temps forts multi-phases plus longs à construire (repris du PRD).
- **NFR-P05** — Déterminisme bit-à-bit conservé (même graine = mêmes positions, mêmes durées, mêmes choix de phases).

## Stratégie de tests

- **TEST-01** — Plancher de durée (20 s) respecté par construction, quel que soit le nombre de phases tirées.
- **TEST-02** — Absence de corrélation mesurée entre durée totale d'un temps fort et son issue, sur pipeline réel.
- **TEST-03** — Continuité aux jonctions de phases (ballon + joueurs), sur un échantillon de temps forts multi-phases.
- **TEST-04** — Déterminisme bit-à-bit sur des temps forts multi-phases.
- **TEST-05** — Non-régression du résultat sportif (score, buteurs, cartons, remplacements strictement identiques avant/après).
- **TEST-06** — La barre de progression ne révèle aucun marqueur de temps fort non encore atteint pendant la lecture.

## Décisions techniques

- **D-001** — Construction multi-phases : habillage narratif pur, aucun nouvel événement réel dans le moteur. **Validé.**
- **D-002** — Barre de progression : marqueurs masqués jusqu'à visionnage. **Validé.**
- **D-003** — Contrat API `/animation` inchangé ; dissimulation traitée côté front uniquement. **Recommandé, à valider.**
- **D-004** — Bibliothèque de phases de construction : un catalogue fixe de l'ordre de 8 à 12 types réutilisables (par exemple : possession adverse, perte de balle/tacle, interception, pressing, faute, transition, récupération haute...), combiné déterministiquement avec les 12 gabarits de conclusion existants, plutôt qu'une génération libre illimitée. **Validé (22/10/2026)** — taille augmentée de 4-6 à 8-12 types pour la variété demandée par le propriétaire.

## Hors périmètre technique

- Toute modification du moteur Poisson (`events.py`, `simulation.py`).
- La persistance de l'état d'une compétition (hors périmètre du PRD).
- Le détail de chaque phase gabarit par gabarit (positions, durées précises) — relève du plan d'implémentation (`/planifie`), pas de ce TRD.
- L'articulation fine avec le chantier « mouvement collectif » en cours : ce TRD suppose sa clôture avant que la construction multi-phases démarre.

## Notes complémentaires

- Risque technique majeur : `templates.py`, `narrative.py`, `sequence_generator.py`, `ball.py`/`motion.py` sont tous sous exception explicite requise par `CLAUDE.md` — toute implémentation nécessitera de demander ces exceptions avant de coder.
- Dépendance d'ordre : ce chantier suppose probablement la clôture du chantier « mouvement collectif » (Phase 5 en attente) et d'A1.1 (inertie), pour ne pas cumuler deux refontes de `motion.py`/`templates.py` en parallèle — à confirmer avec `simulafoot-architect` au moment de planifier.
- D-003 est une recommandation de cadrage, pas une constante déjà validée — à reproposer avant implémentation, comme toute constante produit. D-004 est validé (22/10/2026).
