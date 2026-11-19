# EM-09 — Commandes de vitesse, pause, ralenti (E/V) — 90 min (élevée)

**Status:** livré (19/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : boutons élégants, état actif évident, cohérents avec le HUD ; comportement strictement inchangé.
- **Résultat** : groupe segmenté, bouton pause de 44 px, barre d'espace, badge RALENTI ; `SPEED_OPTIONS` et la boucle intacts.
- **Composants** : `SpeedControls`. **Critères** : chaque vitesse produit exactement la même durée de lecture qu'avant
  (chronométrage d'une minute de match par vitesse, écart < 2 %) ; pause/reprise inchangées ; cibles ≥ 40 px.
- **Tests** : mesure de lecture par vitesse ; test clavier ; captures.
- **Dépendances** : EM-08. **Risques** : raccourci clavier en conflit avec le navigateur.

## Comments

### 19/11/2026 — estimation et constantes validées par le propriétaire

- **Estimation** (travail effectif) : analyse 10 min, développement 40 min, tests 25 min, intégration et vérifications
  15 min, **total 1 h 30**, confiance élevée. Hypothèse : boucle de lecture et `SPEED_OPTIONS` (1, 1,5, 2, 4, 8)
  intacts, seuls les boutons changent. Temps machine à part : suite complète (environ 13 min).
- **Constantes validées (« Je valide », 19/11/2026)** :
  - groupe segmenté unique de 40 px de haut, rayon 8 px, fond `surface-2`, filet `line` ; vitesse active en segment
    plein `accent`, texte blanc ; inactives en gris clair, éclaircies au survol ; libellés « ×1 », « ×1,5 », « ×2 »,
    « ×4 », « ×8 » en Barlow Condensed 600 à 16 px ; 36 px de haut et 14 px sous 960 px de large ou 500 px de haut ;
  - bouton lecture/pause rond de 44 px (40 px sur petit écran), `accent`, séparé du groupe ;
  - ralenti d'un but : badge « RALENTI » rouge au-dessus du groupe, qui sert de bouton « Passer ▸▸ » ; la largeur du
    groupe ne change pas (score centré, EM-08b) ;
  - clavier : barre d'espace = lecture/pause, touches 1 à 5 = les cinq vitesses ; ignoré dans un champ de saisie ;
  - accessibilité : groupe en `radiogroup`, chaque vitesse annoncée avec son état ; bouton « Lecture » / « Pause ».
- **Critères d'acceptation** : durée réelle d'une minute de match par vitesse identique à avant (écart < 2 %) ; pause et
  reprise inchangées ; cibles ≥ 40 px (36 px sur petit écran) ; espace et touches 1 à 5 testées ; score centré, ralenti
  compris ; aucun débordement en 844×390 ; `npm test`, lint 0 erreur, build OK ; suite Python inchangée.
- **Mesure de référence avant le code** (`em09/timing.cjs`, Playwright, trace `buts-nombreux` depuis 10', temps entre
  deux changements de la minute affichée) : ×1 59,998 s, ×1,5 39,998 s, ×2 29,999 s, ×4 14,999 s, ×8 7,500 s
  (théorie 60 / 40 / 30 / 15 / 7,5 s).

### 19/11/2026 — implémentation

- **Code** : `components/match/SpeedControls.jsx` (nouveau : groupe segmenté `radiogroup`, bouton lecture/pause, ligne
  réservée du badge RALENTI · Passer, raccourcis clavier) ; `utils/playbackKeys.js` (fonction pure : touche → action,
  libellés « ×1,5 ») et son test ; `MatchHud.jsx` : les commandes en place sont remplacées par `SpeedControls`, qui
  reçoit les mêmes fonctions du hook. `hooks/useMatchPlayback.js` et `SPEED_OPTIONS` non touchés.
- **Correction en cours de route** : les segments ne faisaient que 34 px de haut (cadre et marge intérieure dans les
  40 px du groupe) ; le filet est désormais dessiné sans prendre de place (`ring-inset`) et chaque segment fait 40 px.
- **Tests** : `utils/playbackKeys.test.js` (4 tests : espace, y compris depuis un bouton ; 1 à 5 dans l'ordre ; rien
  dans un champ de saisie ni avec Ctrl, Cmd ou Alt ; libellés), ajouté au script `npm test`.
- **Mesures** (`em09/check.cjs`, Playwright, serveur de développement, traces réelles `buts-nombreux` et `noms-longs`) :
  - durée réelle d'une minute de match, vitesse choisie au clic : ×1 60,014 s, ×1,5 39,998 s, ×2 29,999 s, ×4
    14,999 s, ×8 7,500 s ; au clavier (touches 1 à 5) : 59,998 / 39,998 / 29,999 / 14,999 / 7,500 s ; référence avant
    le code (vitesse par l'URL) : 59,998 / 39,998 / 29,999 / 14,999 / 7,500 s ; écart maximal **0,03 %** (< 2 %) ;
  - espace : pause (minute figée 8,5 s), reprise (minute qui avance) ; avec le focus sur le bouton ×2, l'espace bascule
    lecture/pause sans changer la vitesse, deux fois de suite (pas de double commande) ;
  - cibles : segments 40 × 40 px (×1,5 : 41 × 40), lecture 44 × 44 px en 1366×768, 1920×1080 et 1100×700 ; 36 × 36 px
    et 40 × 40 px en 844×390 ;
  - centre du score sur celui du terrain (683, 960, 550, 422 px) à l'arrêt **et pendant le ralenti** ; débordement 0 ;
    HUD 89 px (69 px en 844×390), inchangé.
- **Vérifications** : `npm test` 41 passés, 0 échec ; `npm run lint` 0 erreur, 5 avertissements (attendu) ; build OK.
- **À vérifier à l'écran** : rendu du survol des segments ; noms de club très coupés en 844×390 (colonne centrale de
  350 px, voir A2 d'EM-08b).
- **Durée** : estimée 1 h 30 ; réelle environ 45 min de travail effectif (analyse 5, développement 20, tests 15,
  intégration 5), hors temps machine (mesures navigateur environ 12 min, suite complète environ 13 min). Écart − 50 % :
  composant isolé, banc de rejeu et scripts de mesure d'EM-08 réutilisés.

### 19/11/2026 — revue experte, passage 1 : APPROVED_WITH_RESERVATIONS, corrections

- Expert (empreinte `f63af1eb`) : **APPROVED_WITH_RESERVATIONS**. A1 [réserve] touches 1 à 5 lues par `event.key` :
  inopérantes sans Maj sur clavier AZERTY ; A2 [réserve] bouton « RALENTI · Passer » de 20 px de haut (16 px), sous le
  critère des cibles ; A3 [facultatif] espace maintenu (répétition automatique) qui fait alterner lecture et pause ;
  A4 [facultatif] pas de flèches dans le `radiogroup`.
- **Corrections** :
  - A1 : chiffres lus par la position de la touche (`event.code` : `Digit1` à `Digit5`, `Numpad1` à `Numpad5`), repli
    sur `event.key` ; test ajouté (« & é " ' ( » et pavé numérique) ;
  - A3 : touche répétée ignorée (aucune commande) mais interceptée (ni défilement ni clic répété) ; test ajouté ;
  - A2 : **décision du propriétaire (19/11/2026), option « Pause = Passer »** : pendant le ralenti d'un but, le bouton
    rond de 44 px devient « Passer le ralenti » (icône ▸▸) et la barre d'espace passe aussi le ralenti ; le badge
    RALENTI, au-dessus du groupe, n'est plus qu'une information ; pas de pause pendant les quelques secondes du ralenti ;
  - A4 : non traité (facultatif ; les touches 1 à 5 couvrent le besoin).
- **Mesures après correction** (`em09/check.cjs`, navigateur) : pendant le ralenti, bouton « Passer le ralenti » de
  44 × 44 px (40 × 40 en 844×390) ; clic et espace passent le ralenti, badge retiré, lecture qui continue ; AZERTY
  « é » (`Digit2`) → ×1,5, « ( » (`Digit5`) → ×8 ; espace répété : état inchangé. `npm test` 43 passés.

### 19/11/2026 — changement de périmètre : liste des vitesses

- **Décision du propriétaire (19/11/2026)** : « Concernant les vitesses, garde ×1, ×1,5, ×2, ×8, ×32. »
  `SPEED_OPTIONS` passe de `[1, 1.5, 2, 4, 8]` à `[1, 1.5, 2, 8, 32]` (`hooks/useMatchPlayback.js`, seule ligne de
  comportement modifiée ; la boucle de lecture est inchangée). Les touches 1 à 5 suivent le nouvel ordre. Le critère
  « comportement strictement inchangé » vaut désormais pour ×1, ×1,5, ×2 et ×8 ; ×32 est mesuré contre la théorie.
- **Estimation révisée, annoncée avant de continuer** : 1 h 30 → **1 h 50** (développement + 5 min, tests + 15 min :
  mesure de ×32, raccourcis, place en 844×390).
- **Point d'attention signalé au propriétaire** : à ×32, un match se lit en environ 3 min, soit à peu près le temps de
  calcul du moteur en direct ; la lecture rattrapera souvent le calcul (badge « CHARGEMENT… », état d'EM-08).
- **Mesures finales** (`em09/check.cjs` sur le code final) : durée d'une minute de match, au clic : ×1 60,014 s, ×1,5
  39,998 s, ×2 29,999 s, ×8 7,500 s, ×32 1,883 s ; au clavier : 59,998 / 39,998 / 30,015 / 7,500 / 1,867 s ; théorie
  60 / 40 / 30 / 7,5 / 1,875 s ; écart maximal 0,05 % pour ×1 à ×8 (identique à la référence d'avant) et 0,45 % pour
  ×32 (une image à 60 i/s sur 1,875 s) ; AZERTY « ( » (`Digit5`) → ×32 ; cibles, centrage, ralenti et débordement
  inchangés par la nouvelle liste (segments 40 × 40, « ×32 » compris ; 36 × 36 en 844×390 ; débordement 0).
- **Vérifications finales** : `npm test` 43 passés, 0 échec ; lint 0 erreur, 5 avertissements ; build OK ; suite Python
  3 437 passés, 0 ignoré, 14 désélectionnés (775 s).
- **Durée** : estimée 1 h 50 (révisée) ; réelle environ 1 h 15 de travail effectif (analyse 5, développement 30, tests
  30, intégration 10), hors temps machine (bancs navigateur environ 25 min, trois suites complètes environ 39 min). Écart
  − 32 % : composant isolé et bancs d'EM-08 réutilisés ; les réserves de l'expert et le changement de vitesses ont
  ajouté une demi-heure.

### 19/11/2026 — clôture (passage 2)

- Expert : **APPROVED** (empreinte `2fe406a6`) ; A1, A2 et A3 du passage 1 résolues. Réserves facultatives : à ×32, chaque
  but déclenche encore un ralenti de 25 s réelles (comportement du hook, hors périmètre ; passable d'une touche) ;
  flèches non gérées dans le groupe de vitesses (touches 1 à 5 suffisantes).
- Contrôle qualité : **VALIDÉ** (remarque : un lien `?speed=4` est désormais ignoré, cohérent avec le retrait de ×4).
- Décision de clôture : **VALIDÉ** (expert APPROVED, QC VALIDÉ).

