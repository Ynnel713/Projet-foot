# 04k: Duel un contre un : la feinte de frappe ou de passe

**Chantier :** `v2-realisme` (complément de l'audit du dribble, 17/11/2026, demande du propriétaire). **Priorité :** P2. **Catégorie :** exécution et perception.

**Constat vérifié (17/11/2026) :** aucun geste simulé n'existe ; la seule feinte de la feuille de route est le contre-appel sans ballon (`25g`). Un défenseur ne réagit jamais à une frappe ou une passe esquissée : il suit le porteur sans pouvoir être trompé.

**What to build:** face à un défenseur proche qui couvre l'axe de tir ou une ligne de passe, le porteur peut esquisser une frappe ou une passe. Le défenseur y croit ou non : s'il mord, il se fige ou se décale (contre, jambe tendue) pendant un court instant, que le porteur exploite en conduite (04g, 04h) ; s'il n'y croit pas, le porteur a perdu un temps et le défenseur se rapproche. Le défenseur juge la feinte sur ce qu'il perçoit (mémoire de perception, `08b`). Geste tracé et affiché.

**Attributs (ADR 0002, poids à proposer) :**
- porteur, contexte « tenter la feinte » (décision) : Flair, Decisions ;
- porteur, contexte « feinte crédible » (exécution) : Technique, Composure (sous pression, R3) ;
- défenseur, contexte « ne pas mordre » (perception) : Anticipation, Decisions, Concentration (à venir, `v2-collectif/21`).
Sans double comptage avec la lecture de passe (`anticipation.pass_readers`) : la feinte est un effet distinct (réagir à un geste simulé, pas à une passe partie).

**Lien avec l'existant :** complète le découpage de `v2-attributs-restants/07a` (« Flair ajoute les gestes risqués »).

**Blocked by:** 04g (contournement), 04h (crochet), `v2-attributs-contextes/01` et `02` (registre des contextes).

**Bloque :** 04n.

**Status:** à faire (constantes et chiffres réels à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : faible. Hypothèses : l'état « défenseur figé » réutilise le décalage temporaire du crochet (04h) ; la frappe esquissée ne passe pas par `shooting.py` (aucun tir tracé). Au-dessus du seuil de 2 h : découpage à examiner (feinte de frappe, puis de passe).
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Scènes :** défenseur qui couvre l'axe de tir à 2 m : feinte plus fréquente à Flair 99 qu'à 11 ; défenseur à Anticipation 99 mord moins souvent qu'à 11 ; feinte réussie suivie d'une conduite qui élimine plus souvent qu'une conduite directe.
- **Statistiques (50 matchs) :** feintes par match, part réussie, issue de l'action qui suit.

## Acceptance criteria

- [ ] Constantes produit, poids des contextes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Geste tracé et affiché
- [ ] Effets des attributs probabilistes, jamais binaires ; contextes déclarés dans le registre et documentés dans la carte ; pas de double comptage (R1)
- [ ] Scènes et mesure 50 matchs ci-dessus
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
