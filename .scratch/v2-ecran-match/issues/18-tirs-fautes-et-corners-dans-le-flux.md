# EM-D2 — Tirs, fautes et corners dans le flux (D) — 90 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : envoyer à l'écran ce que la trace enregistre déjà.
- **Résultat** : listes `shots`, `fouls`, `restarts` (corners) dans `MatchProgressOut`, comme `goals` aujourd'hui (remplies
  pendant le calcul) ; moteur inchangé.
- **Critères** : réponse allégée (taille mesurée) ; tous les événements portent leur minute (filtrage sur le temps lu).
- **Tests** : `pytest` ; mesure de la charge utile (cible : < 2× la taille actuelle).
- **Dépendances** : aucune. **Risques** : poids de la réponse chaque seconde (n'envoyer que les nouveaux événements).

## Comments

### 19/11/2026 — décision, estimation et critères

- **Constat** : `GET /api/v2/matches/{id}` n'envoie le journal `events` (tirs, arrêts, contres, fautes, remises dont
  corners, hors-jeu, buts) qu'une fois le calcul fini (`api/routers/v2.py:419`, `if done`) ; en direct, l'écran n'a ni
  tirs ni fautes ni corners tant que le moteur n'a pas fini. Bloquant pour EM-14 (statistiques).
- **Décision du propriétaire** (19/11/2026) : « EM-D2 d'abord » (avant EM-14a et 14b).
- **Écart à la spec** (choix technique, sans constante produit) : au lieu de trois listes `shots`, `fouls`, `restarts`,
  le journal `events` existant est envoyé par tranches pendant le calcul, avec son propre curseur `from_event` (comme
  `from_tick` et `from_ball`) : mêmes données qu'en fin de match, causes comprises (tir → arrêt, contre ou but).
- **Estimation** (travail effectif) : analyse 15 min, développement 20 min, tests et mesures 20 min, clôture 15 min,
  **total 1 h 10**, confiance élevée. Temps machine hors total : suite complète.
- **Critères d'acceptation** : tranches mises bout à bout = journal complet, sans trou ni doublon, quel que soit le moment
  du calcul (test pytest sur faux calcul interrompu) ; chaque événement porte sa minute ; réponse finale : seulement les
  événements nouveaux ; charge utile des réponses en direct < 2 × la taille actuelle (mesurée sur trace réelle) ; l'écran
  (`V2Match.jsx`) accumule les tranches ; moteur inchangé ; suite Python 3 437 + nouveaux tests passés ; `npm test`,
  lint 0 erreur, build OK.

### 19/11/2026 — implémentation

- **Code** :
  - `api/routers/v2.py` : `match_progress(..., from_event=0)` ; `MatchProgressOut.first_event` ; `events` envoyés à chaque
    lecture à partir de `first_event` (avant : liste vide tant que le calcul n'était pas fini, puis journal complet) ;
    `_events_out(trace, first=0)` copie la liste avant la tranche (le calcul continue d'écrire). Réponse complète
    (`POST /matches`) inchangée. Moteur inchangé.
  - `ui/src/api/client.js` : `getV2Match(id, fromTick, fromBall, fromEvent)` ; `ui/src/routes/V2Match.jsx` : accumule
    les tranches (`events`) comme les images et la piste du ballon.
- **Tests** : `tests/test_v2engine_trace.py::test_live_match_sends_the_events_in_slices_without_gap_or_duplicate` (faux
  calcul interrompu deux fois au milieu du journal : événements reçus avant la fin, tranches bout à bout = journal
  complet, identifiants contigus, minutes et causes conservées, corner conservé, plus rien de neuf à la fin).
- **Mesures** :
  - charge utile (`mesures/em18-charge-utile.txt`, 3 traces réelles) : journal de 220 à 250 Ko pour 1 542 à 1 730
    événements, soit + 0,72 à + 0,86 % du flux en direct (images + ballon : 29 à 31 Mo) ; la réponse finale ne renvoie
    plus le journal complet (≈ 230 Ko de moins) ;
  - en direct sur l'API réelle (`mesures/em18-direct.py`, Lens–Brest, lecture toutes les secondes pendant 40 s de
    calcul) : 391 événements reçus avant la fin du calcul, jusqu'à 27,2', identifiants contigus, types tir, arrêt,
    contre, faute, remise, etc.
- **Vérifications** : pytest du fichier 15 passés ; `npm test` 77 passés ; lint 0 erreur, 5 avertissements ; build OK ;
  suite Python 3 438 passés, 0 ignoré, 14 désélectionnés (3 437 attendus + 1 nouveau test).
- **Déterminisme** : sérialisation seule ; aucun aléa, aucune horloge.

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `f616245d`) : **APPROVED**. Invariant « sans trou ni doublon » démontré par la structure du journal
  (événements figés, identifiant = position, journal qui ne fait que grandir). A1 [facultatif] l'écran ne filtre pas
  encore les événements sur le temps lu (il ne les affiche pas encore) : à faire en EM-14 avec un test « aucun futur ».
- Contrôle qualité : **VALIDÉ**.
- **Décision de clôture** : VALIDÉ.
- **Attendu de la suite** : 3 438 passés (+ 1 test) ; la ligne « Attendu » de `CLAUDE.md` est à mettre à jour (fichier
  hors suivi documentaire du verrou : à faire à part, avec l'accord du propriétaire).
- **Durée** : estimée 1 h 10 ; réelle environ 1 h (analyse 15, développement 15, tests et mesures 20, clôture 10),
  écart − 14 %. Temps machine hors total : match réel en direct (40 s), suite complète (15 min 52).
