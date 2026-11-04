# 09: Relever la fréquence des mouvements simultanés

**What to build:** aujourd'hui, même pour les postes déjà éligibles à un mécanisme de mouvement, la probabilité de déclenchement par joueur et par clip reste limitée (20-60 % selon l'attribut) — résultat observé par le propriétaire : sur la plupart des clips, seuls 2 joueurs donnent une impression de vrai mouvement. Revoir à la hausse le plancher/la plage de probabilité pour que PLUSIEURS joueurs éligibles se déclenchent simultanément sur un même clip plus souvent, tout en gardant un dosage (jamais 100 %, jamais tous les 22 en même temps non plus).

**Blocked by:** Tickets 01 à 08 de ce dossier (étendre d'abord la couverture à TOUS les postes — y compris ceux qui n'ont aujourd'hui aucun mécanisme ou un mécanisme à moitié couvert — avant d'augmenter la fréquence ; sinon on intensifie un mécanisme encore trop restreint).

**Status:** abandonné (24/10/2026) — V1 gelée sans moteur graphique, effort porté sur la V2 (décision du propriétaire)

- [ ] Sur un échantillon de clips, le nombre moyen de joueurs visiblement en mouvement construit (pas juste en dérive) par clip augmente mesurablement par rapport à l'état actuel
- [ ] **Mesure chiffrée (ajoutée le 23/10/2026, décision propriétaire, interview `/grill-me`)** : sur le pipeline réel (même esprit que `TestPipelineSpeedHeadroom`, ticket 46 de `docs/known_issues.md`), le % d'images où un joueur hors rôle actif reste quasi immobile (déplacement sous un seuil à définir à l'implémentation) diminue mesurablement par rapport à une mesure de référence prise AVANT ce chantier — objective le défaut "majorité figée" remonté par le propriétaire le 23/10/2026, en plus de la validation visuelle ci-dessus
- [ ] Aucun clip ne montre les 22 joueurs en mouvement construit simultané (le dosage reste présent, pas un chaos permanent)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement inchangé
- [ ] Propriétaire valide visuellement, sur un échantillon de clips, que l'impression de collectif vivant est atteinte sans devenir surchargée/artificielle
- [ ] Propriétaire valide la nouvelle plage de probabilité AVANT implémentation (constante produit déjà validée une fois le 16/10/2026, à re-valider pour ce changement)

**Note :** `sequence_generator.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder.
