# 01: Plafond de vitesse partagé par poste (mécanisme commun)

**What to build:** un seul point partagé, dans `motion.py`, qui expose le plafond de vitesse déjà existant par poste (`max_speed_normalized`) comme base commune à TOUT effet qui module la vitesse/amplitude d'un joueur (fatigue, écart de caractéristiques en duel, mouvement riche des joueurs décor). Chaque effet devient un facteur multiplicatif entre 0 et 1 appliqué à ce plafond — jamais un nouveau pourcentage inventé séparément par chantier. Un plancher commun (~70-75 % du plafond du poste) garantit qu'aucun effet, seul ou cumulé avec d'autres, ne fait jamais paraître un joueur totalement à l'arrêt. Les effets se combinent en se multipliant entre eux (jamais en s'additionnant), ce qui borne naturellement le résultat sans plafond séparé à maintenir.

Décisions issues de l'interview du 22/10/2026 (grilling, session forkée) — voir le résumé livré à la session principale pour le détail des échanges.

**Blocked by:** None — ticket racine, démarrable immédiatement, avant tout autre chantier qui en dépend.

**Priorité (23/10/2026)** : chantier prioritaire, à démarrer dès la fin de `temps-forts-multiphases` (Phase 4/ticket 06) — voir `docs/PLAN_PRODUIT.md`, note de pause.

**Status:** livré, validé QC (sous-étape `plafond-vitesse-partage-01`, 23/10/2026, après un REFUSÉ pour un espace supprimé par erreur). Exception `CLAUDE.md` accordée par le propriétaire le 23/10/2026 pour `motion.py` seul.

**Mise en œuvre :** `motion.SPEED_FACTOR_FLOOR = 0.75`, `motion.combined_speed_factor(*facteurs)` (produit des facteurs bornés à [0, 1], `None` neutre, résultat dans [0,75 ; 1]) et `motion.effective_max_speed_normalized(poste, *facteurs)`, appelée par `_raw_position_at`. Aucun effet branché à ce jour : les consommateurs passeront leur facteur à cette fonction.

- [x] Un seul point du code calcule « facteur combiné × plafond du poste » — aucun autre module ne réimplémente ce calcul indépendamment
- [x] Le facteur combiné de plusieurs effets simultanés reste toujours dans `[plancher commun, 1.0]`, quel que soit le nombre d'effets actifs
- [x] Un effet qui ne s'applique pas à un joueur (donnée manquante, hors contexte) renvoie un facteur neutre (1.0), comportement actuel inchangé
- [x] Déterminisme bit-à-bit vérifié
- [x] Résultat sportif strictement inchangé
- [x] Aucune régression sur les gabarits/clips existants (empreinte des payloads de clips de 3 matchs identique au bit près avant/après)
- [x] Propriétaire valide la valeur exacte du plancher commun : **75 %** (tranché le 23/10/2026, interview `/grill-me`, session forkée — marge plus généreuse tant que le mouvement riche vient d'être introduit poste par poste ; resserrable à 70 % plus tard si besoin)

**Note :** `motion.py` est un fichier sous exception (`CLAUDE.md`) — exception à demander au propriétaire avant de coder.

**Consommé par (une fois ce ticket terminé) :** `mouvement-riche-tous-joueurs/01` et `/02`, `style-joueur-animation/02` (écart en duel) et `/03` (fatigue). `style-joueur-animation/01` (fréquence de gabarit) n'en dépend PAS techniquement — il touche uniquement le choix du scénario, jamais la vitesse/amplitude d'exécution.
