# 02: Écart de caractéristiques visible dans un duel 1 contre 1

**What to build:** règle générale, pas limitée à l'attribut vitesse — dans les gabarits de type duel (`profondeur_1v1`, `debordement_centre_tete`, `percee_individuelle`), le ou les attributs PERTINENTS pour la nature du duel (vitesse pour une course de vitesse, mais aussi par ex. équilibre/force pour un contact physique, selon le gabarit) ne dépendent plus seulement du poste des deux joueurs mais de leurs attributs individuels réels (quand disponibles) ; le défenseur adverse directement concerné par le duel est identifié (pas seulement « l'adversaire le plus proche » générique comme aujourd'hui) et ses propres attributs modulent la marge visible du duel — un écart important entre les deux joueurs, sur l'attribut pertinent pour CE duel, doit se voir à l'écran. Le gagnant du duel reste TOUJOURS celui déjà décidé par le moteur (narration/scénario), seule la marge d'exécution varie.

**Blocked by:** `plafond-vitesse-partage/01` (la marge du duel est un facteur appliqué au plafond partagé, pas une règle de vitesse séparée). **Ordre recommandé** (priorité confirmée par le propriétaire, 22/10/2026, pas une dépendance technique au-delà de `plafond-vitesse-partage/01`) : en dernier des 4 chantiers — le plus engageant techniquement, à attaquer une fois les 3 autres mécanismes rodés.

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Sur le même gabarit et la même position de départ, un porteur avec un avantage net sur l'attribut pertinent pour ce duel montre une marge (écart de distance/temps) visiblement plus grande qu'un porteur face à un adversaire de niveau comparable sur ce même attribut
- [ ] La correspondance « quel attribut compte pour quel type de duel » est une table/règle générique validée avec le propriétaire, pas un `if` par gabarit codé en dur
- [ ] Le défenseur identifié comme concerné par le duel est le bon joueur du `Lineup` adverse (pas un décor interchangeable) — vérifiable en traçant l'identité du joueur dont l'attribut est lu
- [ ] Joueur(s) sans attribut individuel disponible (`attributes=None`) : repli sur le comportement actuel basé sur le poste, sans erreur ni régression visible (cohérent avec la règle déjà posée au PRD)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif ET issue du duel scénarisé (qui gagne) strictement identiques à avant — seule la marge d'exécution change
- [ ] Aucune régression sur les gabarits hors duel (les 9 autres gabarits inchangés clip à clip)
- [ ] Le mécanisme consomme le facteur partagé de `plafond-vitesse-partage/01`, ne recalcule pas son propre plafond/plancher
- [ ] Propriétaire valide visuellement, sur un échantillon de duels à écarts de caractéristiques variés, que la différence se voit sans devenir caricaturale

**Note :** `templates.py` et potentiellement `motion.py` (calcul de vitesse max) sont sous exception (`CLAUDE.md`) — exception à redemander explicitement au propriétaire avant de coder, selon les fichiers réellement touchés. Ce ticket touche un mécanisme plus engageant que le 01 (identification précise de l'adversaire concerné dans `sequence_generator.py`, aujourd'hui limité à une proximité générique) — à voir avec le propriétaire si une étude technique courte (TRD) est souhaitée avant de coder.
