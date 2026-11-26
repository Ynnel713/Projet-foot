# 05d: Validation des remplacements : volume, minute, raisons, effet et cohérence avec le score

**Chantier :** `v2-coach-et-gestion-de-match` (audit des remplacements du 26/11/2026, demande du propriétaire, ticket proposé « S5 »). **Catégorie :** validation.

**Constat vérifié (26/11/2026) :**
- Les mesures sont éparpillées :
  - 05a : nombre et minutes, sortants plus fatigués, occasions dans les 15 minutes avant et après ;
  - 05b : part des remplacements offensifs selon le score ;
  - `v2-realisme/20d` : titulaire fatigué contre remplaçant frais, en scène.
- Aucun ticket ne rassemble ces mesures en match sur une série, et trois manquent :
  - les **buts et l'xG** pour et contre après les entrées ;
  - la **contribution des entrants** comparée aux titulaires qu'ils remplacent ;
  - la **raison** de chaque remplacement (05c) confrontée au score.

**What to build:** banc seulement, moteur inchangé. Mesures définies dans `docs/INDICATEURS_V2.md`, ajoutées à `scripts/v2_indicators.py` :
1. **volume** : remplacements et fenêtres par équipe et par match, distribution ;
2. **minute** : premier remplacement, minute moyenne et distribution, part à la mi-temps ;
3. **raisons** : fatigue, carton, performance, consigne, blessure (05c, `v2-attributs-restants/09b`) ;
4. **cohérence avec le score** : profil de l'entrant (offensif, poste pour poste, défensif) selon le score au moment du changement et le style du coach ;
5. **effet** : buts et xG neutre (`v2-realisme/06c`) pour et contre dans les 15 minutes qui suivent une fenêtre, comparés aux 15 minutes qui précèdent et à une série sans remplacement aux mêmes graines ; buts, xG et actions par 90 minutes des entrants contre ceux des sortants sur la même tranche de match.

Rapport sur 50 matchs, avec intervalles de confiance (`v2-realisme/01e`), comparé aux repères réels sourcés ou « non trouvé ». Chaque écart au réel est renvoyé à un ticket, jamais réglé ici. Contrôle : les remplacements ne doivent pas être « magiques » : l'écart de buts après les entrées reste dans l'intervalle du réel, ou est signalé.

**Attributs :** aucun.

**Lien avec l'existant :** ne duplique pas `v2-realisme/20d` (scènes de profils, sans remplacement réel) ; reprend en match les critères de mesure des 05a et 05b au lieu de les recalculer.

**Blocked by:** 05a, 05b, 05c ; `v2-realisme/01e`, `06c` (livrés).

**Bloque :** aucun (passe après la calibration, comme 05b : contrôle de non-régression de `v2-collectif/22c`).

**Status:** à faire (définitions et repères réels à proposer au propriétaire avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et rapport | 25 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : remplacements, fenêtres et raisons tracés par 05a à 05c ; xG neutre déjà au banc. Recherche des repères réels non comptée (environ 30 min).
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs, plus 50 sans remplacement aux mêmes graines.

## Tests

- **Unitaires (traces connues) :** deux changements au même arrêt comptent une fenêtre ; un but 10 minutes après une fenêtre est compté dans « après » ; un entrant offensif à 0-1 est classé « cohérent ».
- **Statistiques (50 matchs) :** rapport publié dans `docs/INDICATEURS_V2.md`, avec intervalles de confiance.

## Acceptance criteria

- [ ] Définitions et repères réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : remplacements par équipe et par match, minute du premier remplacement, part à la mi-temps, buts des entrants
- [ ] Indicateurs reproductibles à graine fixée, testés sur des traces connues
- [ ] Rapport sur 50 matchs : volume, minute, raisons, cohérence avec le score, effet sur buts et xG ; intervalles de confiance ; chaque écart au réel renvoyé à un ticket, jamais réglé ici
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
