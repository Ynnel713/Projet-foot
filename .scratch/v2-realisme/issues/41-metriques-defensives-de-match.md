# 41: Métriques défensives de match : fautes, hors-jeux, relances, buts concédés

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la défense, point 8 « métriques à surveiller sur match » ; découpé du `40` le 24/11/2026, réserve A2 de l'expert). **Priorité :** P2. **Catégorie :** validation.

**Constat vérifié (24/11/2026) :** le banc compte les fautes par match (`v2-collectif/30`), les tacles (`11r`), les contacts (`11e`) et l'origine des buts (`19e`) ; il ne rassemble pas la répartition des fautes par zone et les cartons, les hors-jeux et les situations limites, la réussite des passes défensives et les pertes dans son tiers, ni les buts concédés par type, et ne les compare pas d'un coup aux repères réels.

**What to build:** un rapport de match défensif, sans réglage, par équipe sur 50 matchs : fautes (total, milieu de terrain contre zone dangereuse, dans la surface), cartons (quand `v2-attributs-restants/09a` est livré) ; hors-jeux sifflés et situations limites (attaquant à moins de 0,5 m de la ligne au départ de la passe) ; réussite des passes des défenseurs, pertes dans son tiers et leurs suites (tir concédé dans les 10 s) ; buts concédés par origine (contre, passe dans le dos, coup de pied arrêté, un contre un, `19e`). Chaque métrique a sa définition dans `docs/INDICATEURS_V2.md` et son repère réel (sourcé ou « non trouvé ») ; un écart devient un ticket séparé.

**Attributs :** aucun (mesure).

**Blocked by:** `10j` ; `09k` (volet hors-jeux, si livré) ; `v2-attributs-restants/09a` (volet cartons, si livré). La mesure peut tourner avant sur ce qui existe. **Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : les événements nécessaires sont déjà au journal (`19b`) ; seuls les regroupements et les définitions sont nouveaux. Temps machine, non compté : série de 50 matchs (environ 40 min), suite complète (environ 20 min).

## Acceptance criteria

- [ ] Définitions, zones et repères réels (sourcés ou « non trouvé ») proposés au propriétaire avant le code
- [ ] Rapport sur 50 matchs, par équipe, sans réglage ; écarts signalés en tickets séparés
- [ ] Indicateurs ajoutés au banc et définis dans `docs/INDICATEURS_V2.md`
- [ ] Déterminisme ; suite complète au compte attendu ; durée réelle relevée

## Comments
