# 40: Validation de la défense : niveaux et profils de défenseurs

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la défense, point 7 « faire ressortir les profils et les niveaux » ; le point 8, métriques de match, est au `41`, découpé le 24/11/2026 sur réserve A2 de l'expert). **Priorité :** P2. **Catégorie :** validation.

**Constat vérifié (24/11/2026) :** le banc mesure la défense collective (couverture du presseur, compacité, supériorité locale ; zones et responsabilités prévues au `10j`), les contacts (`11e`), les tacles (`11r`), les fautes (`v2-collectif/30`) et l'origine des buts (`19e`). Aucune mesure ne compare des **défenseurs** entre eux, par niveau et par profil ; les métriques de match sont au `41`.

**What to build:** une validation sans réglage :
- **Niveaux** : même poste, défenseur haut contre bas (Positioning, Anticipation, Marking, Tackling, Decisions, Composure, chacun seul puis ensemble), en scènes fixes et en série : erreurs de placement (écart à sa place, `bloc.positioning_error_m`), passes et appels lus (`anticipation.pass_readers`, `08e`), duels un contre un perdus, embarqué par un leurre (`25e` si livré), fautes et leur zone, relances réussies et pertes sous pression.
- **Profils** (définis par des notes, pas par des étiquettes) : central relanceur (Passing, First Touch, Composure, Vision hautes, Pace moyenne), stoppeur (Aggression, Strength, Tackling hautes), défenseur de couverture (Positioning, Anticipation, Pace hautes), latéral défensif : chacun doit montrer sa signature (relances qui cassent une ligne ; duels tôt et fautes ; interventions en second rideau ; cadrage sur l'ailier, `10l`) et sa contrepartie (exposé dans le dos sur bloc haut ; espaces dans son dos et cartons ; moins de duels gagnés ; couverture intérieure).
- **Métriques de match** : au `41` (fautes, hors-jeux, relances, buts concédés par type) ; ce ticket n'en reprend que ce qui distingue deux défenseurs.
- **Pas de note unique ni de surhomme** : l'effet se répartit entre lecture, placement, duel et relance (R1, ADR 0002) ; le meilleur défenseur se fait encore battre parfois.

**Attributs :** aucun (mesure).

**Blocked by:** `10j` ; `08g`, `09k`, `10l`, `10m` (volets correspondants seulement si livrés ; la validation peut tourner avant sur ce qui existe). **Bloque :** rien (écarts signalés en tickets séparés).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : indicateurs tirés du journal des événements (`19b`) et des traces existantes ; scènes par `tests/scenes.py`. Temps machine, non compté : séries de profils (environ 1 h 30, en tranches de moins de 1 h), suite complète (environ 20 min).

## Acceptance criteria

- [ ] Scènes, profils (jeux de notes), seuils et repères réels (sourcés ou « non trouvé ») proposés au propriétaire avant le code
- [ ] Rapport par niveau et par profil (métriques de match : `41`), sans réglage ; écarts signalés au propriétaire en tickets séparés
- [ ] Tests de garde ajoutés : le meilleur défenseur perd encore des duels ; chaque profil a au moins une contrepartie mesurable
- [ ] Indicateurs ajoutés au banc et définis dans `docs/INDICATEURS_V2.md`
- [ ] Déterminisme ; suite complète au compte attendu ; durée réelle relevée

## Comments
