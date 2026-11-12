# EM-20 — Lisibilité de la hauteur et de l'inclinaison à taille normale (V) — 120 min (moyenne)

**Status:** proposé (09/11/2026) ; création acceptée par le propriétaire le 09/11/2026. **Aucune ligne de code avant son feu vert explicite** : le chantier écran est en attente derrière le moteur.

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).
Origine : réouverture du ticket `v2-hauteur-ballon/01` (09/11/2026). Le verdict visuel du propriétaire à taille normale
est que « l'inclinaison reste imperceptible au premier regard et la cage du filet est illisible sur téléphone (6×4 px) ».
Le ticket 01 est conforme à sa fiche : cette limite vient de la projection sans point de fuite.

- **Objectif** : qu'à taille normale on voie au premier regard que le terrain est vu de biais et que les buts ont une
  hauteur, **sans toucher à la caméra**.
- **Contraintes fixées** :
  - α = 35° figé (« Ne modifie plus l'angle ») ;
  - `project` et `GROUND_MATRIX` inchangés : joueurs et ballon restent aux mêmes points ;
  - pas de perspective (EM-X3 exclu) ;
  - moteur et trace inchangés ;
  - aucun « masquage par un style » : chaque indice doit être une vraie géométrie projetée, ou un ombrage qui suit la
    même projection.
- **Leviers : arbitrage du propriétaire du 09/11/2026.**
  - Retenus : leviers 1 à 4, avec le **levier 4 en priorité** dans l'implémentation (« c'est lui qui rend l'inclinaison lisible sur tout le terrain, pas seulement dans les surfaces »).
  - Reporté : levier 5, à réévaluer après la livraison d'EM-05 et de son dégradé de 6 %, si le critère de contraste du filet n'est pas atteint.
  - Les constantes des leviers restent à valider avant le code.

  Leviers :
  1. **Faces du but ombrées** : filet latéral plus sombre que le toit, pour que la face verticale se détache. Proposé :
     remplissage du filet latéral à 0,35 (aujourd'hui 0,15), poteaux et barre à 0,35 m d'épaisseur.
  2. **Épaisseur minimale à l'écran** : poteaux, barre et arêtes de la cage jamais sous 1 px réel, quelle que soit la
     taille. La géométrie ne change pas, seul le trait s'épaissit (`vector-effect` ou épaisseur calculée depuis l'échelle).
  3. **Drapeaux de coin** : mât de 1,5 m (Lois du jeu, minimum) aux quatre coins, dessiné par `project(x, y, 0 → 1,5)`
     avec un fanion. C'est un repère vertical à chaque angle du terrain.
  4. **Joueurs « sur pied »** : trait fin du point au sol (ombre) jusqu'au rond (1,8 m), par la projection. Il relie le
     rond à son ombre et rend la hauteur lisible. Il complète EM-07 (apparence des marqueurs) sans en changer le rayon,
     l'ombre ni la sélection.
  5. **(Reporté)** **Dégradé de profondeur** : celui d'EM-05 (côté lointain 6 % plus sombre), porté à une valeur à proposer si 6 % ne
     suffit pas.
- **Périmètre** : dessin du terrain et des marqueurs dans `PitchView2` (ex-V2Pitch). Pas de nouvelle donnée d'API.
- **Composants** : `PitchView2`, `GoalFrame`, `PlayerMarker` (après EM-07), `index.css` si besoin d'un jeton.
- **Prérequis** :
  - EM-05 (terrain : teintes, marge réduite à 3 m, donc plus de pixels par mètre) ;
  - EM-07 (marqueurs) ;
  - EM-01 (découpage de `V2Match.jsx`) déjà prévu en amont de ces deux tickets.
  Ce ticket passe **après** eux, pour ne pas refaire leurs choix de couleur et d'échelle.
- **Critères d'acceptation** (posés avant le code, chiffrés ; **validés tels quels par le propriétaire le 09/11/2026**, verdict visuel compris ; ne plus les modifier sans arbitrage) :
  - [ ] Coordonnées intactes : joueurs, ballon et 5 points du terrain (coins, centre, points de penalty) exactement aux
        mêmes positions qu'au commit `f42dc68` (même test qu'EM-05).
  - [ ] Cage du but, mesurée dans le DOM à 844×390 (téléphone en paysage, cible de la spec) : profondeur ≥ 8 px, filet
        latéral ≥ 6 px de haut. À 375 px de large : ≥ 5 px et ≥ 4 px.
  - [ ] Contraste du filet latéral contre le gazon ≥ 3:1 (WCAG, élément graphique).
  - [ ] Si le levier 3 est retenu : chaque mât de coin ≥ 4 px de haut à 844×390.
  - [ ] Fluidité ≥ mesure d'EM-01 (même méthode), nœuds SVG ajoutés ≤ 60.
  - [ ] `npm run build` OK ; `npm run lint` sans nouvelle erreur ni nouvel avertissement.
  - [ ] Verdict visuel du propriétaire sur les captures avant/après aux 4 tailles de la spec : inclinaison et hauteur des
        buts perçues « au premier regard ». C'est un critère de jugement, déclaré comme tel.
- **Tests** :
  - test de projection des 5 points (inchangé) ;
  - mesures DOM des tailles en pixels ;
  - captures avant/après aux 4 tailles ;
  - mesure d'images par seconde.
- **Hors périmètre** : l'angle de caméra, la perspective (EM-X3), la hauteur réelle du ballon (`v2-hauteur-ballon/02b`),
  l'ordre de dessin ballon, buts et gardien (point de vigilance du 02b).
- **Risques** :
  - même avec tous les leviers, une projection orthographique reste proche d'une vue de dessus ;
  - si le verdict visuel reste négatif, la seule piste restante est EM-X3 (perspective), une décision d'architecture.
- **Estimation** (travail effectif) : analyse 20, développement 50, tests 30, intégration et vérifications 20, soit
  **120 min**, confiance moyenne. Hypothèses : EM-05 et EM-07 livrés, leviers 1 à 4 retenus (levier 5 hors estimation), constantes validées en une
  fois. Temps machine hors total : mesure de fluidité, environ 10 min.

## Comments
