# EM-13 — États du match : but, mi-temps, fin (E/V) — 120 min (moyenne)

**Status:** livré (19/11/2026), validé expert + QC

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Résultat** : `MatchBanner` pour but (2 s), mi-temps (3 s, durée actuelle), fin (panneau de fin, bouton Stats et Retour) ;
  badge RALENTI ; coup d'envoi.
- **Critères** : durées du bandeau de mi-temps et du ralenti **inchangées** ; le bandeau ne bloque ni la lecture ni la
  pause ; états vérifiés à x1 et x8.
- **Tests** : trace enregistrée à `t=44`, `t=goal-1`, `t=fin` ; captures des 6 états.
- **Dépendances** : EM-08, EM-12. **Risques** : bandeau qui masque l'action au x8 (durée en temps réel).

## Comments

### 19/11/2026 — décisions, estimation et critères

- **Décisions du propriétaire** (19/11/2026) :
  - bandeau de but « 2 s en temps réel » : sur le haut du terrain, sous le HUD, « BUT · 23' · Kvaratskhelia · club »,
    liseré à la couleur de l'équipe, 2 s réelles quelle que soit la vitesse, sans bloquer lecture ni clics ;
  - fin « Carte centrée » : TERMINÉ, score final, buteurs des deux équipes, bouton Retour (Statistiques avec EM-14),
    terrain visible autour, carte refermable pour revoir la position finale ;
  - coup d'envoi « Au début seulement » : « COUP D'ENVOI » 2 s réelles au lancement, rien à la reprise ;
  - découpage : « Un seul ticket ».
  - Déjà décidé par la spec (§ Interactions, validée le 07/11/2026) : mi-temps = bandeau centré plus discret, même durée
    (3 s), score, sans masque noir total ; ralenti signalé par un badge RALENTI à côté de la minute.
- **Choix de détail (à confirmer à l'écran)** : badge RALENTI à la place de EN DIRECT pendant un ralenti, en `accent`
  (priorité : TERMINÉ, MI-TEMPS, RALENTI, CHARGEMENT, EN DIRECT) ; un bandeau en pause reste affiché et disparaît à la
  reprise une fois ses 2 s écoulées ; un saut de lecture (départ à `t`) n'annonce pas les buts d'avant.
- **Estimation** (travail effectif) : analyse 15 min, développement 50 min, tests et mesures 35 min, clôture 20 min,
  **total 2 h**, confiance moyenne (au seuil indicatif : découpage proposé, refusé par le propriétaire). Temps machine
  hors total : suite complète, mesures navigateur, banc de rejeu.
- **Critères d'acceptation** :
  - durées inchangées : bandeau de mi-temps 3 s réelles (le match attend, comme avant), ralenti (2 s après le but, 8 s
    avant, × 0,4) ; instants de mi-temps et de ralenti identiques à avant sur trace réelle ;
  - bandeau de but : un par but, au moment où le score change, 2 s réelles (± 0,1 s) à × 1 et × 8, texte juste ; aucun
    au départ d'une lecture lancée après des buts ;
  - aucun bandeau ne bloque la lecture, la pause ni les clics sur le terrain (`pointer-events: none`) ;
  - mi-temps : plus de masque noir plein terrain, score affiché ; fin : carte avec score, buteurs et Retour, refermable ;
    ligne « Match terminé » de la zone basse retirée ;
  - badge RALENTI pendant le ralenti seulement ;
  - captures des 6 états (coup d'envoi, en cours, but, ralenti, mi-temps, fin) ; `npm test`, lint 0 erreur, build OK ;
    suite Python 3 437 passés.

### 19/11/2026 — implémentation

- **Code** :
  - `hooks/useMatchPlayback.js` : `goalBanner` (indice du but annoncé) et `kickoffBanner`, 2 s en horloge réelle
    (`EVENT_BANNER_MS`), posés et retirés dans la boucle sans toucher à l'instant lu (`next`) ; `begin` réputé annoncés
    les buts d'avant `start` et n'affiche le coup d'envoi que pour un départ à 0 ; ralenti et mi-temps inchangés ;
  - `components/match/MatchBanner.jsx` (nouveau) : `TopBanner` (but, coup d'envoi ; liseré d'équipe), `HalfTimeBanner`
    (carte centrée, sans masque), `FullTimeCard` (TERMINÉ, score, buteurs, Retour, fermer) ; bandeaux sans pointeur ;
  - `MatchScreen.jsx` : bandeaux et carte sur le terrain ; masque noir de mi-temps et ligne « Match terminé » retirés ;
  - `utils/matchHud.js` : badge RALENTI (`accent`, après TERMINÉ et MI-TEMPS), `goalBannerText` ; `MatchHud.jsx` : ton
    `accent`.
- **Tests** : `utils/matchHud.test.js` : ordre des badges adapté (RALENTI ajouté), + 2 tests (priorité du badge
  RALENTI, texte du bandeau avec csc et buteur inconnu) ; `npm test` 77 passés.
- **Mesures en lecture réelle** (`mesures/em13-mesure.cjs`, trace `em11-om-ol`, relevé toutes les 25 ms, résultats
  `em13-apres.json`, captures `em13/` : coup d'envoi, en cours, but, ralenti, mi-temps, fin) :
  - but : bandeau 2,00 s à × 1 et 1,95 s à × 8, apparu à l'image même où le score change (écart 0 ms), « BUT · 2' ·
    OPENDA · OLYMPIQUE LYON » ; aucun bandeau pour une lecture lancée à 2,1' (après le but) ;
  - coup d'envoi : 1,81 s relevées (relevé commencé après l'affichage ; 2 s par construction) ;
  - mi-temps : 3,03 s à × 8, badge MI-TEMPS, carte sans masque ;
  - badge RALENTI : 25,05 s à × 1 (= (8 + 2) s / 0,4), absent hors ralenti ;
  - fin : carte « TERMINÉ | OLYMPIQUE MARSEILLE | 6-3 | OLYMPIQUE LYON | Gouiri 9', 29', 71', 90+5' | Abdelli 74' |
    Paixão 83' | Openda 2', 7', 16' | Retour », boutons Fermer et Retour, fermée au clic ; plus de ligne « Match
    terminé » en zone basse ;
  - pointeur : `pointer-events: none` sur les bandeaux, l'élément sous le centre du bandeau est le terrain.
- **Lecture inchangée** (banc de rejeu d'EM-01 à horloge synthétique, harnais `mesures/em13-harnais-rejeu.js` au
  résumé indépendant de la mise en page : score, minute, bouton « Passer le ralenti », MI-TEMPS ; builds de production
  avant `ffd865d` et après ; trace `em11-om-ol` complète à × 8) : 20 256 images, 134 changements visibles, journaux
  **identiques** (`em13-rejeu-avant.json`, `em13-rejeu-apres.json`) : instants de but, de ralenti et de mi-temps
  inchangés.
- **Vérifications** : lint 0 erreur, 5 avertissements ; build OK ; suite Python 3 437 passés, 0 ignoré, 14
  désélectionnés.
- **Déterminisme** : affichage seul ; durées des bandeaux en horloge réelle (comme la mi-temps), sans effet sur l'instant
  lu.
- **Constaté en passant (hors périmètre)** : défaut d'EM-08c, la largeur minimale du nom (4,5 rem) laisse un blanc après
  un nom court (« Openda      2', 7', 16' ») : correctif en EM-08d.
- **À vérifier à l'écran** : la carte de fin masque le centre du terrain (refermable) ; lisibilité du bandeau de but sur
  la pelouse ; bandeau de but et badge RALENTI simultanés à × 8.

### 19/11/2026 — revue experte (passage 1), contrôle qualité et clôture

- Expert (empreinte `2c19fb9e`) : **APPROVED**. A1 [facultatif] `endClosed` n'est pas remis à zéro par `begin` (sans
  effet aujourd'hui : écran démonté au retour) ; A2 [facultatif] en pause à 0', le bandeau COUP D'ENVOI reste affiché
  jusqu'à la première image jouée (règle choisie).
- Contrôle qualité : **VALIDÉ** (captures non ouvertes par le QC : lisibilité renvoyée à l'écran).
- **Décision de clôture** : VALIDÉ.
- **Durée** : estimée 2 h ; réelle environ 1 h 50 de travail effectif (analyse 15, développement 40, tests et mesures 40,
  clôture 15), écart − 8 %. Temps machine hors total : mesures navigateur en lecture réelle, deux builds et deux rejeux
  complets image par image (environ 40 min en parallèle), suite complète (14 min 55).
