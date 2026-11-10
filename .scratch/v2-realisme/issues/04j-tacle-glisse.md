# 04j: Le tacle glissé

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (dernier recours défensif, avec son risque). **Catégorie :** exécution.

**Constat vérifié :** un seul tacle, debout, tenté à moins de 1,5 m (`match.TACKLE_RADIUS_M`).

**What to build:** Le défenseur peut tenter un tacle glissé quand le porteur s'échappe (au-delà de la portée du tacle debout, dans une portée allongée) : chance de gagner le ballon plus faible à distance, risque de faute plus élevé, défenseur au sol plus longtemps s'il rate. Tackling règle la réussite ; la fréquence relève d'Aggression et, plus tard, de « Dives Into Tackles » (09a).

**Attributs :** Tackling (réussite) ; Aggression (fréquence, déjà branchée)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/07a` : tacle glissé ; termine la découpe (choix et diversité des gestes vérifiés ici).

**Blocked by:** 04g (Duel un contre un : le contournement).

**Bloque :** 21b ; `v2-mise-en-scene/05` (ajouté le 10/11/2026, audit de la roadmap).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : faute et gravité réutilisent `duel.foul_severity`.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** porteur qui s'échappe à 2,5 m : glissé possible ; à 1 m : tacle debout
- **Statistiques (séries de matchs) :** 50 matchs : chaque geste du duel (contournement, crochet, protection, glissé) apparaît, aucun ne dépasse la part validée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Geste tracé et affiché
- [ ] Fautes et défenseur au sol tracés
- [ ] Diversité des gestes vérifiée sur 50 matchs
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
