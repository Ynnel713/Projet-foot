# 01: Fréquence des gabarits pondérée par le style déclaré du joueur

**What to build:** règle générale, pas une liste figée de cas particuliers — pour un but marqué par un joueur dont les « gestes préférés » (`preferred_moves`) sont renseignés, CHAQUE geste déclaré augmente la fréquence du ou des gabarits cohérents avec lui (ex. un geste évoquant le dribble favorise `percee_individuelle`/`debordement_centre_tete`, un geste évoquant le tir lointain favorise les gabarits à tir lointain — ces deux exemples illustrent la règle, ils ne la limitent pas : toute correspondance geste ↔ gabarit pertinente suit le même mécanisme). Jamais systématique, toujours un dosage (fréquence relative). Étend la pondération déjà existante de `pick_template` (`templates.py`), ne la remplace pas.

**Blocked by:** None techniquement (ce ticket ne touche que le CHOIX du scénario, jamais la vitesse/amplitude — pas de dépendance sur `plafond-vitesse-partage/01`, à la différence des autres tickets de ce dossier). **Ordre recommandé** (priorité confirmée par le propriétaire, 22/10/2026, pas une dépendance technique) : après `mouvement-riche-tous-joueurs` et après le ticket 03 (fatigue) de ce dossier.

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Sur un grand échantillon de buts simulés, un joueur avec un style « dribble » déclaré obtient le gabarit `percee_individuelle`/`debordement_centre_tete` dans une proportion mesurablement plus élevée qu'un joueur sans ce style (comparaison statistique, pas cas isolé)
- [ ] Le même joueur n'obtient PAS ce gabarit à chaque but — la fréquence reste dosée, jamais 100 %
- [ ] Un joueur sans `preferred_moves` renseigné (cas majoritaire aujourd'hui, voir note PRD US-17) suit exactement le comportement actuel, sans régression ni erreur
- [ ] Déterminisme bit-à-bit vérifié (même sha256 que le reste du module, jamais `random`/`hash()`/horloge)
- [ ] Résultat sportif (score, buteur, passeur) strictement identique — seul le CHOIX du scénario de mise en scène change
- [ ] La règle est générique (une table de correspondance geste → gabarit(s), pas du code au cas par cas par geste) — ajouter un nouveau geste ne doit pas demander de nouvelle branche de code, juste une nouvelle ligne de table
- [ ] Propriétaire valide la table complète de correspondance geste préféré → gabarit(s) favorisé(s) et l'amplitude du dosage AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `templates.py` est un fichier sous exception (`CLAUDE.md`) — exception à redemander explicitement au propriétaire avant de coder ce ticket précis (l'exception donnée pour le ticket 01 de `temps-forts-multiphases` ne couvre pas ce chantier séparé).

**Limite connue à rappeler au propriétaire avant de lancer ce ticket :** `preferred_moves` est vide pour la plupart des joueurs de la base actuelle (voir `docs/PRD_PRODUIT.md`, note US-17) — l'effet ne sera visible que sur une minorité de joueurs tant que cette donnée n'est pas étendue par un scraping plus large (hors scope de ce ticket).
