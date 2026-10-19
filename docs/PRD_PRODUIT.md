# PRD — Simulafoot (cadrage produit global)

## Problème

Il n'existe pas d'outil de simulation de football réaliste, narratif et en français, accessible à un utilisateur occasionnel. Les jeux existants sont souvent en anglais, complexes, ou peu narratifs. Le porteur du projet veut un outil personnel qui simule des championnats au niveau joueur, avec des matchs racontés et rejoués de façon crédible, pour son propre usage quotidien et à partager occasionnellement avec des proches.

## Solution

Simulafoot simule des compétitions de football (championnats, Coupe du Monde, Ligue des Champions, compétitions personnalisées) à partir d'une base de joueurs réels avec profils et attributs détaillés. Chaque match produit un score, des statistiques et un fil de commentaire enthousiaste en français — le calcul du résultat reste quasi instantané. Les temps forts d'un match joué peuvent ensuite être revisionnés sous forme d'animation 2D crédible : chaque temps fort ne montre pas seulement le geste décisif (tir, but) mais raconte la construction de l'action — récupération, perte de balle, contre-attaque, faute, coup de pied arrêté — sur une durée variable et imprévisible, pour donner l'impression d'un vrai résumé de match plutôt qu'une succession de highlights isolés. Le score se découvre au fil du visionnage, jamais annoncé d'avance. L'ensemble est consultable depuis une application web (PWA), utilisable sur ordinateur comme sur mobile.

## Utilisateur cible

Le porteur du projet (Olivier), développeur et utilisateur principal, usage quotidien, qui fait tourner l'application en local. Des proches occasionnels, connaisseurs de football, qui consultent les résultats et regardent les matchs de façon occasionnelle — aujourd'hui uniquement quand le porteur du projet leur montre l'application en local ; l'accès à distance (serveur, lien partagé) n'est pas encore défini.

## User Stories

1. En tant que porteur du projet, je veux simuler une journée ou une saison complète d'un championnat, afin de suivre l'évolution d'une compétition comme dans un jeu de manager.
2. En tant que porteur du projet, je veux consulter le classement en direct d'une compétition, afin de savoir où en est chaque club.
3. En tant qu'utilisateur, je veux consulter la fiche d'un joueur (profil, attributs, note), afin d'évaluer son niveau et son style.
4. En tant qu'utilisateur, je veux regarder l'animation 2D des temps forts d'un match joué, afin de revivre ses moments clés de façon crédible.
5. En tant qu'utilisateur, je veux lire le fil de commentaire live d'un match, afin d'en suivre le déroulement sans forcément regarder l'animation.
6. En tant que porteur du projet, je veux créer une Compétition Perso (clubs et sélections mélangeables, format libre), afin de simuler des confrontations qui m'intéressent spécifiquement.
7. En tant qu'utilisateur, je veux simuler la Coupe du Monde et la Ligue des Champions avec leurs formats réels (poules, barrages, élimination directe), afin de vivre ces compétitions telles qu'elles existent.
8. En tant que proche occasionnel, je veux pouvoir regarder un résumé de match (score, buteurs, temps forts) que me montre le porteur du projet, afin de suivre les résultats sans connaître le détail technique.
9. En tant qu'utilisateur, je veux consulter l'application sur mobile aussi bien que sur ordinateur, afin de pouvoir suivre une compétition où que je sois.
10. En tant qu'utilisateur, si un match n'est pas animable (données insuffisantes), je veux une explication claire plutôt qu'un échec silencieux, afin de comprendre pourquoi je ne peux pas le revoir.
11. En tant qu'utilisateur, je veux qu'un joueur ou un club sans données détaillées (attributs, style d'entraîneur) se comporte normalement plutôt que de casser l'expérience, afin que les trous de données ne soient jamais visibles comme des bugs.
12. En tant qu'utilisateur, je veux que la composition de chaque match tienne compte des blessures, suspensions et cartons en cours, afin que l'enchaînement des journées reste crédible.
13. En tant qu'utilisateur, je veux que chaque temps fort me montre la construction de l'action (comment elle démarre, se développe et se conclut) et pas seulement le geste final, afin que ça raconte une vraie histoire de jeu plutôt qu'un instantané.
14. En tant qu'utilisateur, je veux que la durée d'un temps fort ne me permette jamais de deviner s'il va se conclure par un but, afin de garder le suspense à chaque visionnage.
15. En tant qu'utilisateur, je veux découvrir le score au fil du visionnage des temps forts plutôt que de le voir annoncé d'avance, afin de vivre le match comme un vrai résumé plutôt qu'un spoiler.
16. En tant qu'utilisateur, je ne dois jamais savoir à l'avance combien de temps forts compte un match, ni si celui que je regarde est le dernier, afin de ne jamais anticiper la fin du match pendant le visionnage.

## Critères de succès

- Le calcul du résultat d'un match (score, buteurs, événements) reste quasi instantané, quelle que soit la richesse des temps forts affichés ensuite.
- Chaque temps fort animé dure entre 10 et 40 secondes, jamais moins de 10 secondes.
- Sur un échantillon de temps forts, la durée ne permet pas de deviner l'issue : pas de corrélation mesurable entre durée et but marqué.
- Un match produit entre 10 et 20 temps forts, chacun pouvant enchaîner plusieurs phases de jeu avant sa conclusion.
- Rien dans l'interface ne permet de déduire, avant qu'il ne se termine, le nombre de temps forts restants ou si le temps fort en cours est le dernier du match.
- L'animation d'un match s'ouvre en moins de 10 secondes au premier chargement (sans cache).
- Les 9 championnats, la Coupe du Monde, la Ligue des Champions et une Compétition Perso sont simulables de bout en bout, résultats et classements inclus.
- Pour une graine donnée, deux simulations du même scénario produisent exactement le même résultat (score, buteurs, cartons, remplacements) à chaque exécution.
- Toutes les interactions et tous les textes produits sont en français.
- Aucune formule, distribution ou constante de gameplay n'est modifiée sans validation explicite préalable du porteur du projet.

## Hors périmètre

- Compte utilisateur, authentification, multijoueur.
- Sauvegarde nommée d'une partie ou persistance disque de l'état d'une compétition entre deux lancements — la perte au redémarrage reste assumée.
- Partage à distance (serveur, cloud, lien accessible par des proches sans que le porteur du projet fasse tourner l'application) — non défini pour l'instant.
- Simulation physique « en direct » d'un match : l'animation rejoue toujours un résultat déjà décidé, jamais un match simulé en temps réel.
- Streamlit comme interface activement développée — reste présent à titre historique, la PWA React est la seule référence officielle.
- Comparateur de joueurs, export de données, statistiques avancées (xG détaillé, heatmaps, percentiles).
- Contrôle direct d'une équipe ou d'un joueur pendant un match.
- Multilingue — français uniquement.
- Audit ou certification d'accessibilité formelle (niveau AA) — pas une priorité vu l'usage réel.
- Calcul d'une « note FM » dédiée — abandonné ; « Moyenne joueur » reste la seule note qui alimente le moteur.

## Décisions d'implémentation

- La PWA (web, utilisable sur ordinateur et mobile) est la seule interface de référence ; Streamlit n'est plus développé.
- Un match n'est animable que s'il a été joué avec une composition réellement enregistrée ; sinon, l'écran indique explicitement pourquoi l'animation n'est pas disponible plutôt que d'échouer silencieusement.
- Le rendu animé suit le référentiel visuel d'un jeu de manager sportif classique (type Football Manager 2D) : la crédibilité perçue prime sur la précision métrique exacte.
- Le commentaire live est toujours produit, quel que soit le mécanisme utilisé en coulisses ; un repli automatique garantit qu'il n'y a jamais d'écran vide faute de génération de texte.
- Un joueur ou un club pour lequel une donnée détaillée manque (attributs, style d'entraîneur) se comporte de façon neutre par défaut, jamais en erreur ni en blocage visible.
- Le résultat affiché (score, buteurs, cartons, remplacements) est strictement identique entre le classement/les statistiques et l'animation rejouée du même match : jamais de divergence visible entre les deux.
- La durée de chaque temps fort est tirée aléatoirement entre 10 et 40 secondes, indépendamment de son issue (but ou non), pour qu'aucun signal de durée ne permette de deviner le résultat à l'avance.
- Un temps fort peut enchaîner plusieurs phases de jeu distinctes (perte de balle, transition, faute, coup de pied arrêté…) avant sa conclusion, plutôt que de démarrer directement sur le geste décisif.
- Le nombre total de temps forts d'un match et leur répartition dans le temps ne sont jamais révélés à l'avance ; rien dans l'interface n'indique, pendant le visionnage d'un temps fort, qu'il s'agit du dernier.

## Notes complémentaires

- **Changement majeur, pas un ajustement mineur** : les gabarits actuels (12 scénarios figés par type d'événement) scriptent chacun un seul geste décisif, sans enchaîner plusieurs phases de jeu. Construire cette narration multi-phases est un chantier à part entière, à cadrer techniquement (TRD/plan dédié) avant toute implémentation — ce PRD fixe l'attente produit, pas la solution technique.
- Risques connus à surveiller : dépendance à un site tiers (fminside.net, structure non garantie, protection anti-robot) pour les attributs détaillés des joueurs ; données joueurs mises à jour à la main à chaque nouveau patch FM, sans pipeline automatique ; projet personnel mené seul, risque de perte de motivation dans la durée.
- Ce PRD cadre le produit dans son ensemble. Il coexiste avec des PRD de chantier plus ciblés (par exemple `docs/PRD.md`, dédié au chantier « mouvement collectif » du rendu animé, actuellement en cours ailleurs) qui détaillent une fonctionnalité précise sans contredire ce cadrage global.
- L'ancien PRD v1.0 (`docs/PRD – Simulafoot.pdf`, 10/10/2026) décrivait une intention très différente de l'état réel du produit (moteur action par action, note FM, base SQLite, front React/TypeScript). Ces écarts restent documentés à titre historique dans le TRD (section 13) ; ce nouveau PRD fait foi pour le cadrage produit actuel.
