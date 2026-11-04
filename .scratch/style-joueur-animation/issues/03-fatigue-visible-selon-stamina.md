# 03: Fatigue visible (Stamina) au fil du match

**What to build:** le mouvement d'un joueur (vitesse/amplitude) se dégrade visiblement à mesure que le match avance, modulé par son attribut `Stamina` individuel (quand disponible) — un joueur très endurant garde une allure proche de son niveau de début de match même tard dans la rencontre ; un joueur peu endurant montre un mouvement visiblement plus lent/moins ample dans les temps forts tardifs (ex. 80ᵉ minute) que dans les mêmes situations en début de match. S'appuie sur la minute déjà disponible par clip (`clip.metadata.minute`). **Portée tranchée avec le propriétaire (22/10/2026) : effet PUREMENT visuel sur l'animation — n'influence jamais les probabilités du moteur Poisson ni le résultat sportif.** La fatigue est un SEUIL de déclenchement qui dépend de `Stamina` (un joueur endurant reste à 100 % jusqu'à tard, un joueur peu endurant décroche plus tôt) — pas une pente progressive dès la 1ʳᵉ minute (décision de l'interview du 22/10/2026).

**Blocked by:** `plafond-vitesse-partage/01` (consomme directement le facteur de vitesse partagé). Indépendant des tickets 01 et 02 de ce dossier entre eux. Séquencé APRÈS `mouvement-riche-tous-joueurs` (01, 02 et 03) — ordre de priorité confirmé par le propriétaire (22/10/2026), et les deux chantiers touchent le même fichier (`motion.py`), donc à ne pas paralléliser.

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Sur le même gabarit/rôle, un joueur à `Stamina` faible montre un mouvement mesurablement plus lent/moins ample à une minute tardive du match qu'à une minute précoce
- [ ] Un joueur à `Stamina` élevée ne montre pas de dégradation visible (ou très limitée) sur la même comparaison
- [ ] Joueur sans attribut `Stamina` disponible : comportement neutre par défaut, identique au comportement actuel (cohérent avec la règle déjà posée au PRD)
- [ ] Résultat sportif (score, buteurs, cartons) strictement inchangé — la fatigue n'est jamais lue par le moteur Poisson, uniquement par le rendu
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Aucune régression sur les clips/gabarits hors du mécanisme de fatigue
- [ ] Le mécanisme consomme le facteur partagé de `plafond-vitesse-partage/01`, ne recalcule pas son propre plafond/plancher
- [ ] Propriétaire valide le seuil de déclenchement (minute × Stamina → début de la dégradation) AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `motion.py` et potentiellement `templates.py` sont sous exception (`CLAUDE.md`) — exception à redemander explicitement au propriétaire avant de coder.
