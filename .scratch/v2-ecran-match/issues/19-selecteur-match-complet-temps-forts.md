# EM-19 — Sélecteur « Match complet / Temps forts » dans le HUD (E/V) — 90 min (moyenne)

**Status:** à faire (demande du propriétaire, 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md`.

- **Objectif** : un bouton, dans le HUD, qui permet de choisir entre regarder le **match complet** et ses **temps forts**.
- **Problème** : l'écran V2 n'a qu'un lecteur continu. Les modes de visionnage (Match complet, Buts, Moments clés, Résumé)
  sont prévus par le chantier `v2-mise-en-scene` ; son ticket `01` construit le lecteur et un sélecteur provisoire, sans
  design. Ce ticket-ci donne au sélecteur sa place et son habillage dans la refonte de l'écran, il ne calcule aucun moment.
- **Résultat** : groupe segmenté à deux positions « Match complet » · « Temps forts » à côté des commandes de vitesse,
  même hauteur et même état actif que `SpeedControls` ; choix avant le lancement et en cours de lecture ; la vitesse
  courante est conservée ; « Match complet » est le mode par défaut.
- **Périmètre** : présentation et câblage du composant sur le lecteur de `v2-mise-en-scene/01` (mode actif, changement de
  mode). **Hors périmètre** : découpage des moments, barre de progression et boutons précédent/suivant (ticket
  `v2-mise-en-scene/01`), contenu des modes (tickets `02` et `03`). Tant que le mode « Temps forts » n'existe pas, la
  position est visible mais grisée, avec l'info-bulle « bientôt disponible » (rien n'est simulé).
- **Correspondance à confirmer** : « Temps forts » = le mode **Résumé** (environ 10 minutes, 8 à 12 moments selon l'intérêt
  du match), recommandé car c'est ce que la télévision appelle des temps forts. Alternative : **Moments clés** (grosses
  occasions, buts et cartons rouges seulement), plus court et plus sélectif. Les deux autres modes (Buts, Moments clés)
  pourront s'ajouter au même sélecteur sans changer sa forme.
- **Composants** : `ModeSelector` (nouveau, dans `components/match/`), `MatchHud`.
- **Critères d'acceptation** : cible tactile ≥ 40 px ; état actif identique aux vitesses ; changement de mode en cours de
  lecture sans changer la vitesse ni afficher de score ou de repère futur (règle sans spoiler de `v2-mise-en-scene`) ;
  position « Temps forts » grisée et non cliquable tant que le mode n'est pas livré ; aucune modification de la boucle de
  lecture par ce ticket ; capture à 4 tailles, build et lint OK.
- **Tests** : captures des deux états (Match complet actif, Temps forts grisé puis actif une fois livré) ; test clavier ;
  vérification que la vitesse choisie survit au changement de mode (quand le lecteur existe).
- **Dépendances** : EM-08 (HUD), EM-09 (commandes) ; `v2-mise-en-scene/01` (lecteur et modes) pour que le bouton fasse
  quelque chose ; `v2-mise-en-scene/03` (Résumé) ou `02` (Moments clés) pour que « Temps forts » soit sélectionnable.
- **Risques** : deux tickets de deux chantiers touchent le même sélecteur. Le premier livré crée le composant, l'autre
  l'adapte ; ne pas écrire deux sélecteurs.

## Comments
