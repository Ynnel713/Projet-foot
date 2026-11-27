# 22: Régression de fluidité de l'écran de match V2 (− 21 % depuis le ticket hauteur-ballon/01)

**Ouvert le 27/11/2026** (décision du propriétaire, « ok », à la clôture du `v2-hauteur-ballon/02b2`).

**Constat (02b2, mesure sans affichage, processeur ralenti 6 fois, même match, vitesse ×1, 30 s après 10 s de lecture ; script `.scratch/v2-hauteur-ballon/mesures/02b2-fps.js`, résultats `02b2-fps-resultats.jsonl`)** :

| État | Images par seconde |
|---|---|
| `41e573e` (base du 02b) | 59,9 |
| `f42dc68` (ticket hauteur-ballon/01) | 59,9 |
| `1923ec0` (avant le 02b) | 45,9 (4 passages alternés) |
| final du 02b2 | 47,3 (4 passages alternés) |

Le 02b ne coûte rien de mesurable ; la perte (environ − 21 %, des images de plus de 50 ms apparaissent) est entre `f42dc68` et `1923ec0` : 25 commits qui touchent l'écran (`git log f42dc68..1923ec0 -- ui/src/components/match ui/src/utils ui/src/hooks ui/src/routes/V2Match.jsx`), dont `v2-correctifs-ecran/04a-04b` (piste fine, Catmull-Rom), `v2-ecran-match/04` à `21b` (écran en trois zones, bancs, marqueurs en relief, ballon dessiné et traînée avec `<defs>` reconstruits à chaque image, filet qui ondule, HUD, frises, compositions, statistiques).

**What to build:**
1. **Bissection** sur ces 25 commits avec le même banc (réponses d'API figées, `02b2-fixture-fps.py`), 3 passages par état ; identifier le ou les commits responsables et la part de chacun.
2. **Correction** ciblée du coût (sans changer ce qui est affiché), ou, si le coût est inhérent à un choix d'affichage validé, proposition chiffrée au propriétaire.
3. Mesure finale : baisse de 10 % au plus par rapport à `41e573e` (critère du 02b2, non tenu à sa clôture).

**Blocked by:** aucun.

**Bloque :** aucun.

**Estimation** (27/11/2026) : analyse 15 min, bissection (pilotage, lecture) 30 min, correction 30 min, tests et intégration 15 min ; total 1 h 30 ; confiance faible (cause inconnue). Temps machine à part : environ 5 états × 3 passages × 50 s, plus suite complète.

**Status:** à faire

## Acceptance criteria

- [ ] Commit(s) responsable(s) identifié(s) par bissection, part de chacun chiffrée
- [ ] Fluidité finale ≥ 90 % de celle de `41e573e` sur le même banc (ou écart accepté par le propriétaire sur proposition chiffrée)
- [ ] Affichage inchangé (captures avant / après sur les mêmes instants)
- [ ] `npm run build` OK, `npm run lint` sans nouvelle erreur, `npm test` vert ; suite complète au compte attendu ; V1 inchangée

## Comments
