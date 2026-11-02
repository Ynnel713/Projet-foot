# 02: Cadre de navigation (espace de compétition, Reprendre, fin du cul-de-sac)

**What to build:** Lot 2 de la refonte UX/UI (direction validée le 01/11/2026, lancement du lot 2 le 02/11/2026 : « Oui »). Donner à chaque compétition un espace à onglets toujours visible, permettre de reprendre la compétition en cours depuis l'accueil (même après rechargement de la page), et ne plus jamais renvoyer l'utilisateur à l'accueil quand il clique sur un match.

**Status:** livré (02/11/2026), validé expert + QC

**Constats de l'audit traités**
- Pas de navigation de compétition : on circule avec « Accueil » et des « Retour » (`navigate(-1)`).
- Le contexte (« Ligue 1 » dans l'en-tête) et la compétition en cours sont perdus au rechargement ; l'accueil ne propose pas de reprendre.
- Cliquer sur un match joué ouvre `/pitch`, désactivé en V1, qui redirige vers l'accueil en remplaçant l'historique : la compétition est perdue.

**Décisions de conception (dans la direction validée)**
- Onglets selon le format, pour n'exposer que des écrans qui existent :
  - championnat : Journée · Classement · Stats ;
  - poules + élimination (LdC, Coupe du Monde, perso hybride) : Phase de ligue ou Poules · Phase finale (active une fois lancée) · Stats ;
  - élimination directe : Tableau · Stats.
- L'onglet « Clubs » prévu par la proposition arrive au lot 5, avec l'écran club : on accède aux clubs depuis les classements et les matchs d'ici là.
- Barre d'onglets en bas sur mobile, colonne à gauche sur bureau (≥ 768 px), titre de la compétition toujours visible.
- `/competition/:id` ouvre le bon onglet selon le format et la phase ; « Reprendre » y mène.

**Hors périmètre (volontairement)**
- `MatchRow.jsx`, `Groups.jsx`, `Bracket.jsx`, `Simulation.jsx` : modifications non commitées du chantier animation ; non édités (leurs boutons « Retour » / « Classement » internes disparaîtront au lot 3). Les lignes de match restent cliquables ; la feuille de match qui leur servira de destination arrive au lot 4.
- Persistance des compétitions côté API (une compétition disparaît au redémarrage de l'API) : décision API en attente du propriétaire. Côté interface, une compétition introuvable (404) est simplement oubliée.

## Critères d'acceptation

- [x] `/competition/:id` redirige vers Journée (championnat), Phase de ligue/Poules ou Phase finale selon `knockout_started` (hybride), Tableau (élimination directe)
- [x] Onglets visibles sur toutes les pages de la compétition (journée, classement, stats, poules, phase finale, club, joueur), onglet actif mis en évidence ; « Phase finale » inactive tant que l'élimination n'a pas commencé, active sans rechargement juste après « Lancer les barrages »
- [x] Mobile 375 px : barre d'onglets en bas, cibles ≥ 44 px, aucun défilement horizontal de page ; bureau : colonne à gauche
- [x] Compétition active (id, libellé) conservée après rechargement de la page ; en-tête qui affiche toujours son nom
- [x] Accueil : carte « Reprendre » (nom, progression) si une compétition active existe encore côté API ; absente sinon ; une réponse 404 efface la compétition mémorisée, une erreur réseau non
- [x] Clic sur un match joué : l'utilisateur reste dans sa compétition (plus jamais l'accueil), y compris au rechargement direct d'une URL `/pitch`
- [x] Classement et Stats : boutons « Retour » supprimés (remplacés par les onglets)
- [x] `npm run build` OK ; `npm run lint` : 0 erreur, 5 avertissements au plus
- [x] Parcours vérifiés à l'écran, bureau et mobile : championnat, LdC (phase de ligue → barrages), compétition perso à élimination directe, Reprendre après rechargement
- [x] Aucun fichier interdit par CLAUDE.md ni fichier Python touché

## Comments

**02/11/2026 — implémentation**
- Fichiers : `ui/src/components/layout/CompetitionLayout.jsx` (nouveau), `App.jsx` (routes imbriquées sous `/competition/:id`), `store/useGameStore.js` (persist zustand, stockage tolérant aux échecs d'écriture), `api/client.js` (erreur porteuse de `status`), `routes/Home.jsx` (carte « Reprendre »), `routes/PitchView.jsx` (redirection), `routes/Standings.jsx` et `routes/Leaderboards.jsx` (Retour supprimés), `components/layout/Header.jsx` (commentaire).
- Build OK ; lint 0 erreur, 5 avertissements (préexistants).
- Parcours vérifiés au navigateur (bureau 1440 px) : championnat créé, `/competition/:id` → Journée ; clic sur un match joué → reste sur Journée ; onglets Classement et Stats ; rechargement → en-tête « Ligue 1 » et carte « Reprendre » (« Journée 1 / 34 ») → clic → Journée ; identifiant inconnu → 404 → mémoire effacée, carte absente ; API arrêtée → mémoire conservée, carte masquée. LdC lancée depuis l'accueil : « Phase de ligue » active, « Phase finale » inactive, puis active et courante sans rechargement après « Lancer les barrages » ; `/competition/:id` → Phase finale une fois l'élimination lancée. Compétition perso à élimination directe : Tableau + Stats, nom « Compétition perso ». URL `/pitch` ouverte directement : poule → Phase de ligue, tour → Phase finale.
- Mobile 375 px (mesuré dans la page) : barre d'onglets en bas, 3 onglets de 125 × 56 px, colonne latérale masquée, largeur de contenu 375 px pour 375 px d'écran (aucun défilement horizontal).
- Revue `simulafoot-reviewer` : accepter, de préférence après correction du point 1. Corrigés : (1, majeur) après lancement de la phase finale, un clic sur un match de poule renvoyait sur Phase finale → la redirection de `/pitch` choisit l'onglet selon les paramètres du match (poule, tour, journée), vérifié à l'écran ; (2) une erreur passagère ne masque plus les données déjà chargées ; (3) données et erreurs étiquetées par compétition ; (4) un 404 tardif sur l'accueil ne peut plus effacer une compétition lancée entre-temps ; (5) échec d'écriture du stockage local ignoré ; (6) une compétition introuvable ouverte par URL est oubliée ; (7) commentaire de `Header.jsx` ; onglet inactif marqué `aria-disabled`.
- Reporté au lot 3 (fichiers du chantier animation, non édités ici) : la mention « Champion » de la colonne n'apparaît qu'au changement d'onglet suivant ; `Groups.jsx` propose encore « Lancer les barrages » quand l'élimination a déjà été lancée ailleurs ; les boutons « Retour » internes de Groups et Bracket.

**02/11/2026 — passage 1 de /valider-ticket-simulafoot** (base 316d2ef, empreinte f984d578…)
- Expert : APPROVED. Facultatif : A1 doublon d'historique après un clic sur un match (« Précédent » semble sans effet au premier appui ; disparaît au lot 4 avec la feuille de match) ; A2 un appel `getCompetition` (et `getGroups` en hybride) par changement d'onglet, voulu.
- QC (`refonte-ui/02`) : VALIDÉ. Non bloquant : pas de test JS automatisé ; reports au lot 3 consignés.
- Clôture : VALIDÉ (cloture.py decision, journal `refonte-ui/02/cloture`).
