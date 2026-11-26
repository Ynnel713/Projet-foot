# 01f: Lecteur : modes, enchaînement des moments, carton de contexte

**Chantier :** `v2-mise-en-scene` (audit du mode « moments clés », 26/11/2026). **Catégorie :** écran.

**Constat vérifié (26/11/2026) :** la lecture est dans `ui/src/hooks/useMatchPlayback.js` (EM-01), vitesses ×1, ×1,5, ×2, ×8, ×32 (EM-09), score révélé au but, ralenti d'un but (EM-13). Le sélecteur de mode à quatre positions est le ticket `v2-ecran-match/19`.

**What to build:**
1. **Modes** branchés sur le sélecteur d'EM-19 : Match complet (existant), Buts, Moments clés, Résumé. Modes autres que Match complet grisés tant que le calcul n'est pas fini (01e).
2. **Enchaînement** : le lecteur joue la fenêtre de chaque moment puis saute au suivant ; boutons précédent et suivant ; la vitesse choisie est conservée ; changer de mode en cours de lecture reprend au premier moment qui suit la minute lue (ou à la minute lue en Match complet).
3. **Carton de contexte** avant chaque moment (contre « contexte manquant ») : minute, score avant le moment, équipe qui attaque, durée courte ; jamais d'information future (issue, score après).
4. **Sans spoiler** : le score affiché est celui d'avant le moment jusqu'à l'instant du but ; le ralenti et le bandeau de but d'EM-13 jouent normalement.

**Attributs :** aucun.

**Constantes à proposer avant le code :** durée du carton de contexte ; transition entre deux moments (coupure franche ou fondu court).

**Blocked by:** 01e ; `v2-ecran-match/19` (composant du sélecteur, livré d'abord avec les modes grisés : ordre décidé le 19/11/2026).

**Bloque :** 01g, 02, 03.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible. Hypothèses : la boucle de `useMatchPlayback` accepte un saut de minute sans réécriture (le banc EM-00 le fait déjà avec `?t=`) ; tests unitaires du séquenceur sous node, comme `momentum.js`.
Temps machine, non compté : suite complète (environ 10 min) ; captures sur les 3 traces du banc EM-00 (empreintes vérifiées avant comparaison).

## Tests

- Séquenceur testé sous node : ordre, précédent, suivant, reprise après changement de mode, fin de liste.
- Banc EM-00 (`buts-nombreux`, `sans-but`) : mode Buts sur le 0-0 annonce qu'il n'y a aucun but ; sur 3-3, six moments dans l'ordre.
- Contrôle visuel : carton de contexte sans score futur ; vitesse conservée.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Les quatre modes lisibles, modes autres que Match complet grisés pendant le calcul
- [ ] Précédent, suivant, changement de mode testés ; vitesse conservée
- [ ] Carton de contexte avant chaque moment, sans information future (vérifié sur les 3 traces)
- [ ] Rejeu Match complet identique image par image à avant (non-régression, comme EM-13)
- [ ] `npm run build` OK, `npm run lint` sans erreur nouvelle
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
