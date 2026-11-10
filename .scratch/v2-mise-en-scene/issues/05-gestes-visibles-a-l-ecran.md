# 05: Gestes visibles à l'écran : chute, tacle glissé, plongeon, filet

**Chantier :** `v2-mise-en-scene` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P3 (l'écran montre ce que le moteur a vraiment produit, rien de plus). **Catégorie :** rendu.

**Constat vérifié :** l'écran V2 dessine des ronds et un ballon (`ui/src/components/match/V2Pitch.jsx`) ; le filet est dessiné mais fixe ; aucun joueur au sol, aucun plongeon.

**What to build:** Postures tirées des seuls événements de la trace (19b) : tacle glissé et joueur au sol (04j, 12c), plongeon du gardien vers le point d'arrêt (05b), joueur à terre après une faute, filet qui se creuse au point d'entrée du ballon, d'autant plus que le ballon va vite. Aucune posture sans l'événement correspondant.

**Attributs :** aucun

**Blocked by:** `v2-realisme/19b`, `v2-realisme/04j` ; `v2-hauteur-ballon/02b`.

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 1 h |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : formes simples en SVG, sur la projection existante.
Temps machine, non compté : aucun ; vérification dans le navigateur.

## Tests

- **Unitaires :** chaque posture n'apparaît que si l'événement est dans la trace (rejeu d'une trace enregistrée, EM-00)
- **Écran :** but, tacle glissé et arrêt plongeant regardés sur une trace réelle

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Aucune posture sans événement
- [ ] Filet qui réagit au point et à la vitesse d'entrée
- [ ] `npm run build` et `npm run lint` OK (0 erreur)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
