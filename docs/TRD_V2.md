# TRD — Simulafoot V2 (moteur physique piloté par les attributs joueurs)

> Traduit techniquement les user stories 27 à 29 de `docs/PRD_PRODUIT.md`. Ne couvre pas l'architecture V1 (moteur Poisson, narration, `canvas.html`) — inchangée, voir `docs/TRD_SIMULAFOOT.pdf` + `docs/TRD_MAJ.md`. Toutes les décisions ci-dessous viennent d'une session `/grill-me` avec le porteur du projet (24/10/2026, session forkée) ; le détail du raisonnement derrière chacune est dans l'historique de cette conversation.

## Contexte technique

La V1 calcule le résultat d'un match par un moteur statistique (Poisson, par équipe), puis l'anime : le rendu rejoue toujours un résultat déjà décidé, jamais recalculé. La V2 inverse ce principe : un moteur physique 2D, piloté par les 47 attributs réels de chaque joueur (`data/joueurs.xlsx`), détermine lui-même l'issue du match — façon Football Manager. La V1 reste strictement inchangée et jouable ; la V2 est un chantier entièrement nouveau, pas une évolution de l'existant.

Référence de conception pour chaque attribut : `Guide_attributs_joueurs.pdf` (fourni par le porteur du projet). Il couvre les 47 attributs (Physique ×8, Mental ×14, Technique ×10, Coups de pied arrêtés ×4, Gardien ×11) et pose 5 règles de conception à respecter pour chacun : probabiliste jamais binaire, courbe non linéaire (effet quasi neutre entre 45 et 55, amplifié vers les extrêmes), le contexte module la note (pression, fatigue, score, enjeu), l'importance dépend du poste, un attribut a souvent une contrepartie (ex. Aggression : plus de duels gagnés, plus de cartons).

## Architecture & composants

- **Module entièrement séparé** : nouveau package côté API, nouvelles routes, nouvelle entrée UI (« Version 2 (bêta) ») — aucun fichier protégé actuel (`simulation.py`, `narrative.py`, `narrative_player.py`, `events.py`/`ball_events.py`, `animation/types.py`, `serialize.py`, `motion.py`, `sequence_generator.py`, `ball.py`, `templates.py`, `render/canvas.html`) n'est modifié. Nom de package exact à fixer au moment du premier ticket (hors périmètre de ce TRD).
- **Réutilisation en lecture seule** : `clubs.py`, `players.py`, `lineup.py` (chargement des joueurs, meilleure compo par club, groupes de postes) ne sont pas protégés et sont réutilisés tels quels par V2. `season.py`/`standings.py`/`schedule.py`/`groups.py`/`knockout.py`/`champions_league.py`/`custom_competition.py` (eux non plus pas protégés) seront réutilisés plus tard pour brancher les compétitions, hors périmètre du premier jalon.
- **Calcul physique continu, à plat (x/y)** : positions, vitesses et détection de collision des 22 joueurs et du ballon, sans hauteur modélisée. Les duels aériens (centre, tête, corner) sont résolus par un tirage pondéré par les attributs concernés (Jumping Reach, Heading, Aerial Reach, Taille FM), pas par une vraie trajectoire en cloche — réversible plus tard si besoin (voir Hors périmètre).
- **Résolution des actions discrètes** (duel, tacle, tir, passe) par tirage pondéré par les attributs pertinents des joueurs impliqués, au moment du contact/de la proximité, en respectant les 5 règles du guide (probabiliste, courbe non linéaire, contexte, poste, contrepartie) — superposée au mouvement continu, pas une alternative à lui.
- **Pondération par poste, mécanisme partagé** : une seule table poste → poids par attribut (ex. Tackling pesant lourd pour un DM, presque rien pour un ST), construite une fois et consommée par toute la résolution d'actions, jamais réimplémentée ticket par ticket.
- **Calcul côté serveur (Python)** : le moteur produit une trace complète du match (position de chaque joueur et du ballon à chaque tick, + événements horodatés), calculée une fois. Le rendu 2D (navigateur) se contente de la rejouer à vitesse réglable — même forme que le pipeline V1 (calcul puis rejeu), mais la trace est physique/continue au lieu d'être narrative/scénarisée.
- **Deux modes sur le même moteur** : « regarder » (rejeu de la trace à un rythme proche d'un match, vitesse ajustable, façon Football Manager) et « tout simuler sans regarder » (même moteur, rendu sauté) — les deux doivent coexister, le second étant la fonctionnalité déjà appréciée en V1 (simuler une saison d'un coup).
- **IA de déplacement, phase 1** : placeholder volontairement simpliste (chaque joueur rejoint sa position de formation, ou le ballon s'il en est proche) — pas de vraie prise de décision (Decisions/Vision/Off the Ball/Teamwork) avant que le mouvement et les collisions de base fonctionnent.
- **Données manquantes** : même principe que la V1 (US-11, `docs/PRD_PRODUIT.md`) — un joueur sans donnée détaillée se comporte de façon neutre par défaut, jamais en erreur. Pertinent dès le premier ticket : `Pieds` vide pour 61 % des lignes de la base, `Weak foot` manquant pour 526 joueurs (source : `Guide_attributs_joueurs.pdf`).

## Données & modèle

- Lit la même base que la V1 (`data/joueurs.xlsx`, via `clubs.py`/`players.py`) : les 47 attributs, `Weak foot`, `Pieds`, `Taille FM`, `Preferred moves`, `Postes FM naturels`.
- Nouveau : table statique poste → poids par attribut (définie en code, comme le catalogue de gabarits de `templates.py` en V1 — pas une donnée persistée).
- Nouveau : format de trace de match (positions x/y des 22 joueurs + ballon par tick, événements horodatés) — à spécifier au moment du premier ticket (déplacement).
- Aucune nouvelle source de données externe.

## Sécurité & confidentialité

Inchangé — aucune nouvelle donnée personnelle, aucun nouvel accès réseau externe.

## Performance & fiabilité

- **NFR-V01** — Le mode « tout simuler sans regarder » reste praticable pour une saison complète (34 journées) sans attente excessive : même moteur que le mode « regarder », le rendu seul est sauté, pas un moteur allégé séparé (risque de divergence entre les deux modes sinon).
- **NFR-V02** — Un match « regardé » démarre son affichage dans un temps raisonnable. Pas de seuil chiffré à ce stade (l'équivalent V1, NFR-P04, est 10 s) — à fixer au premier ticket de rendu, une fois le format de trace connu.
- **NFR-V03** — Déterminisme assoupli : contrairement à la V1 (NFR-P05, bit-à-bit garanti), la V2 n'offre pas de garantie de reproductibilité exacte. Décision explicite du porteur du projet (24/10/2026) : implication acceptée — un bug ne sera pas forcément rejouable à l'identique pour vérification.
- **NFR-V04** — Chaque comportement visible d'un joueur dérive d'au moins un attribut réel de sa fiche (US-27, critère de succès du PRD) : aucune action générée indépendamment des données.

## Stratégie de tests

- **TEST-V01** — Un écart d'attribut extrême entre deux joueurs (ex. Pace 99 vs 10) produit un écart mesurable et dans le bon sens sur le comportement résultant (ex. le plus rapide gagne la course), conforme aux fiches de `Guide_attributs_joueurs.pdf`.
- **TEST-V02** — Après chaque ticket V2, la suite de tests V1 reste intégralement verte et aucun fichier protégé n'est modifié (`git diff` sur la liste protégée vide).
- **TEST-V03** — Le mode batch produit un résultat exploitable (score, événements) sans rendu, sur un échantillon de matchs.
- **TEST-V04** — Un joueur avec des données manquantes (`Pieds`/`Weak foot` absents) se comporte de façon neutre, jamais en erreur ni en blocage visible.

## Décisions techniques

- **D-V01** — Module V2 entièrement séparé, zéro fichier protégé V1 modifié. **Validé.**
- **D-V02** — Réutilisation en lecture seule de `clubs.py`/`players.py`/`lineup.py`/`coaches.py` (`coaches.py` ajouté le 02/11/2026 avec la levée de D-V10) (et plus tard `season.py`/`standings.py`/`schedule.py`/les modules de compétitions). **Validé.**
- **D-V03** — Physique continue à plat (x/y), pas de hauteur de ballon pour l'instant ; duels aériens résolus par tirage pondéré. **Validé, révisable plus tard** (le porteur du projet a formulé ce choix comme « dans un premier temps »). **Révisée le 03/11/2026** : le moteur calcule la hauteur du ballon (`z`, `vz`, gravité, rebonds) ; les joueurs restent à plat, un saut est un événement de la trace ; le duel aérien garde un tirage pondéré, entre les seuls joueurs capables d'atteindre le ballon. Étude `docs/ETUDE_HAUTEUR_V2.md`, chantier `.scratch/v2-hauteur-ballon/`.
- **D-V04** — Calcul server-side Python ; trace complète calculée une fois, rejouée ensuite par le rendu à vitesse réglable façon Football Manager. **Validé.**
- **D-V05** — Les deux modes (regarder / tout simuler sans regarder) coexistent sur le même moteur. **Validé.**
- **D-V06** — Déterminisme assoupli pour la V2 (pas de garantie bit-à-bit), contrairement à la règle dure de la V1. **Validé**, divergence de règle assumée.
- **D-V07** — Table de pondération attribut × poste : mécanisme partagé, construit une fois, consommé par toute la résolution d'actions. **Validé.**
- **D-V08** — Premier ticket de déplacement : IA placeholder (position de formation / vers le ballon), pas de vraie prise de décision avant que le mouvement de base fonctionne. **Validé.**
- **D-V09** — Premier jalon jouable : un seul match isolé, pas encore branché aux compétitions existantes. **Validé.**
- **D-V10** — Influence des coachs sur le moteur V2 : différée à l'origine. **Levée par le porteur du projet le 02/11/2026** : les styles du coach (Contre attaque, Pressing, Défensif, Offensif, Possession) orientent le comportement collectif, la gestion du score et les remplacements. Chantier : `.scratch/v2-coach-et-gestion-de-match/`.
- **D-V11** — Découpage en tickets : un ticket par attribut (jusqu'à 47), ordonnés essentiels d'abord (déplacement → contact/passes → duels/tacles → tirs/gardien, un match complet devient jouable dès cette étape) puis attributs dispensables (coups de pied arrêtés spécialisés, tendances gardien, Leadership...). **Validé** — détail des tickets : `docs/PLAN_V2.md`.
- **D-V13** — Flux aléatoires par sous-système (05/11/2026, ticket `v2-realisme/01a`) : chaque sous-système tire dans son propre `random.Random` (`v2engine/flux.py`), semé au coup d'envoi par sha256 de « base|nom du flux », la base étant un seul tirage du module `random`. Une graine posée par `random.seed` reste la seule graine d'un match ; ajouter ou retirer un tirage dans un sous-système ne décale plus les autres, ce qui rend attribuables les écarts entre deux profils. Complète D-V06 sans la contredire (pas de garantie bit-à-bit entre versions, reproductibilité à graine fixée). Migrés au 01a : perception, décision ; au 01b, tous les autres (duel, passe, tir, placement, défense, arbitrage) : plus aucun tirage du moteur dans le module `random` hors la base du match. **Validé** par le propriétaire le 05/11/2026 (« Oui, valide D-V13 »), après le ticket 01a (`f5fd059`). D-V12 est réservée au ticket `v2-collectif/28c`.

## Hors périmètre technique

- Toute modification des fichiers protégés V1 (liste complète : voir `CLAUDE.md`).
- Vraie physique 3D (effet du ballon, vent, physique verticale des joueurs), perspective avec effet de fuite — hors périmètre (D-V03 révisée : seule la hauteur du ballon est simulée).
- Branchement sur les compétitions existantes (championnat, poules, Coupe du Monde, Ligue des Champions, Compétition Perso) — différé après le premier match isolé (D-V09).
- Contrôle tactique de l'utilisateur pendant un match (choix de tactique en direct, changements) — hors périmètre, comme en V1.
- Garantie de déterminisme bit-à-bit — explicitement non retenue pour la V2 (D-V06).
- Tick rate / granularité exacte du pas de temps physique, nom du package, format exact de la trace de match — paramètres d'ingénierie à trancher au premier ticket d'implémentation, pas dans ce TRD.

## Notes complémentaires

- Points d'attention sur la base réelle à garder en tête à l'implémentation (source : `Guide_attributs_joueurs.pdf`) : colonne `Pieds` vide pour 61 % des lignes, `Weak foot` manquant pour 526 joueurs ; les tendances gardien (Eccentricity, Punching, Rushing Out) ne sont **pas** des indicateurs de qualité — à ne jamais pondérer comme telles ; les attributs mentaux sont globalement hauts et peu différenciants dans la base actuelle (Determination/Work Rate/Teamwork ~60-64) — un modèle linéaire naïf risque de produire des comportements trop uniformes, d'où la courbe non linéaire exigée par le guide.
- Risque déjà identifié pour la V1 et qui s'applique autant sinon plus à la V2 (projet personnel mené seul, risque de perte de motivation dans la durée, voir `docs/PRD_PRODUIT.md`) : le découpage essentiels-d'abord (D-V11) vise justement à produire un match jouable le plus tôt possible plutôt que d'attendre la fin des 47 tickets.
- Ce TRD ne couvre que le premier jalon (un match isolé). Les étapes suivantes (branchement aux compétitions, coachs, physique 3D) feront l'objet de mises à jour de ce document ou de TRD dédiés, selon leur ampleur — à trancher le moment venu.
