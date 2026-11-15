# 11n: Le porteur qui perd un contact peut perdre le contrôle du ballon (Balance)

**Chantier :** `v2-realisme` (constat du ticket 11i, 15/11/2026 ; décision du propriétaire « Créer un ticket moteur »). **Priorité :** P1. **Catégorie :** physique.

**Constat vérifié (11i, 50 matchs, `docs/INDICATEURS_V2.md` section 48) :** perte de balle sans faute dans les 3 s qui suivent un contact perdu par le porteur, par tranche de Balance : 16,6 % (moins de 50, n = 404), 14,4 % (50-64), 12,4 % (65-79), 17,1 % (80+, n = 420) ; les extrêmes ne se distinguent pas (± 3,6 points). La Balance ne réduit que la vitesse perdue et le délai avant d'agir (délai avant l'action : 1,15 s à moins de 50, 0,80 s à 80+). Code : `match._unsettle` ne touche jamais au ballon du porteur (vitesse réduite, décision repoussée seulement).

**What to build:** Un porteur qui perd un contact franc peut voir le ballon lui échapper (ballon libre près de lui, poussé dans le sens du contact), avec une probabilité qui baisse avec sa Balance. Dans `match._unsettle` ou à côté, sans toucher aux fichiers protégés. Le duel d'épaule (11c) et le tacle gardent leurs propres règles : vérifier la règle anti double comptage (`docs/CARTE_ATTRIBUTS_V2.md`, Balance déjà lue par 12c).

**Attributs :** Balance (porteur) ; éventuellement l'écart de Strength du contact (11b), à trancher.

**Constantes à proposer avant le code (valeurs indicatives, non validées) :** probabilité d'échappée au contact perdu, de 25 % à Balance 1 à 5 % à Balance 99 ; vitesse du ballon échappé 2 à 4 m/s. Chiffre réel : à chercher (part des pertes de balle sur contact en Ligue 1) ou « non trouvé ».

**Blocked by:** 11i (livré).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : un point d'application (`_unsettle`) ; le ballon échappé réutilise l'état « ballon libre » existant ; pas de faute nouvelle.
Temps machine, non compté : série appariée de 50 matchs (une série à la fois : mémoire) ; suite complète.

## Acceptance criteria

- [ ] Banc d'abord (réserve A1 de l'expert au 11i, acceptée par le propriétaire : « corriger au 11n ») : un tir de l'équipe du porteur dans la fenêtre de 3 s (arrêt, sortie de but, but) clôt la fenêtre sans perte (`Collector._close_carrier_windows`) ; test : porteur bousculé qui tire à 1 s puis sortie de but adverse, aucune perte ; série « avant » remesurée avec ce banc
- [ ] Constantes et chiffre réel (sourcé ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scènes : porteur à Balance basse qui perd le contact : ballon échappé plus souvent qu'à Balance haute (tirages à graine fixée) ; contact gagné : rien
- [ ] 50 matchs appariés contre `11i-serie.txt` : perte sans faute en 3 s décroissante avec Balance, écart des extrêmes significatif
- [ ] Sans régression significative sur buts, tirs, passes réussies, pertes de balle (rapportées), temps de jeu effectif
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
