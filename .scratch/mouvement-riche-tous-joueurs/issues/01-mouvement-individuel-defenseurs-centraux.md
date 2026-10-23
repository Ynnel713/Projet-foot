# 01: Mouvement individuel réel pour les défenseurs centraux

**What to build:** aujourd'hui, les défenseurs centraux (DC) ne bougent qu'en bloc, via une seule ligne collective qui se décale (`_cb_line_drift`) — aucun mouvement individuel distinct d'un DC à l'autre. Chaque DC doit avoir un mouvement individuel cohérent avec son rôle (couverture, suivi d'un attaquant, ajustement de profondeur selon la phase de jeu), sans pour autant quitter sa zone de responsabilité comme le ferait un attaquant. S'appuie sur le mécanisme déjà construit (`docs/PLAN.md`, chantier mouvement collectif) plutôt que d'en créer un nouveau.

**Blocked by:** `plafond-vitesse-partage/01` (le mouvement du DC doit respecter le plafond/plancher partagé, pas réinventer sa propre règle de vitesse).

**Status:** livré, validé QC (sous-étape `mouvement-riche-tous-joueurs-01`, 23/10/2026) — reste la validation visuelle du propriétaire

- [ ] Sur un même clip, les 2 (ou 3) DC d'une même équipe montrent des trajectoires individuelles mesurablement différentes l'une de l'autre (pas la même ligne translatée)
- [ ] Le mouvement reste dans l'amplitude et la zone réalistes d'un DC (pas de montée façon attaquant) — validé visuellement par le propriétaire
- [ ] Joueur sans attribut individuel disponible : repli sur le comportement actuel, sans erreur
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement inchangé
- [ ] Aucune régression sur les autres postes/gabarits
- [ ] Le mécanisme consomme le facteur partagé de `plafond-vitesse-partage/01`, ne recalcule pas son propre plafond/plancher
- [ ] Propriétaire valide l'amplitude/les règles de mouvement du DC AVANT implémentation (constante produit, règle `CLAUDE.md`)

**Note :** `sequence_generator.py`/`motion.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder.

**Exception accordée (23/10/2026) :** `sequence_generator.py` seul (`motion.py` non modifié).

**Décisions du propriétaire (23/10/2026) :**
- Constantes : 3 m de déplacement max, couloir latéral ±3 m, profondeur 0 à 2 m (jamais dans l'autre sens), suivi si l'attaquant est à moins de 15 m.
- Les DC des DEUX équipes bougent individuellement : l'équipe qui défend recule, celle qui attaque monte légèrement (même plage 0-2 m).
- Dépassement accepté et documenté : 7 DC sur 1 869 (0,37 %) dépassent 3 m d'au plus 0,7 m, uniquement à cause de l'écartement anti-collision (`motion._apply_avoidance`, mécanisme commun inchangé) ; la trajectoire calculée du DC ne dépasse jamais 3 m.

**Mise en œuvre :** `_cb_individual_drift` (sequence_generator.py) : dérive de ligne partagée conservée (compacité) + parts individuelles à sels propres (couverture vers l'axe pour le DC loin du ballon, suivi vers le point où l'action se termine — position de l'attaquant qui conclut, choisie pour rester identique entre `enrich_with_background` et `opponent_field_tracks` —, profondeur). Pas de probabilité ni d'attribut : le critère « joueur sans attribut » est sans objet. Aucune règle de vitesse propre : vitesse vérifiée sous `motion.effective_max_speed_normalized("DC")`.

**Mesure (pipeline réel, graine d'audit, 30 matchs, 1 032 paires de DC) :** écart max de déplacement entre DC d'une même équipe, médiane 0,48 → 1,52 m (p90 0,80 → 2,42 m) ; amplitude médiane 0,64 → 1,73 m ; vitesse max 56 % du plafond, 0 dépassement.
