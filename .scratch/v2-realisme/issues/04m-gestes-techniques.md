# 04m: Duel un contre un : les gestes techniques (passement, petit pont, roulette, double contact)

**Chantier :** `v2-realisme` (complément de l'audit du dribble, 17/11/2026, demande du propriétaire). **Priorité :** P2. **Catégorie :** exécution.

**Constat vérifié (17/11/2026) :** aucun geste technique n'existe ; le geste préféré « Tries Tricks » de la base est rattaché au ticket `v2-attributs-restants/05` sans mécanisme sur lequel s'appuyer.

**What to build:** une famille de gestes techniques du porteur face à un défenseur proche, chacun avec sa situation et son effet :
- **passement de jambes** : déséquilibre le défenseur d'un côté (décalage latéral temporaire) avant un contournement ;
- **petit pont** : le ballon passe entre les jambes d'un défenseur de face et immobile ou presque ; le porteur le reprend derrière lui (ballon libre entre deux touches, 04f) ;
- **roulette** : pivot qui met le corps entre le défenseur et le ballon en changeant de direction, au contact (lien avec la protection, 04i) ;
- **double contact** : déplacement latéral court du ballon qui sort de la portée du tacle.
Gain plus grand qu'un dribble simple s'il réussit, perte plus probable s'il rate (geste difficile). Gestes tracés et affichés.

**Ajout du 24/11/2026 (demande du propriétaire du 24/11/2026, éléments sur la technique, point 2).** Le passement couvre aussi la feinte de corps sans toucher le ballon (épaule, faire croire à un côté) ; le défenseur trompé entre dans l'état unique de déséquilibre du `04o`.

**Attributs (ADR 0002, poids à proposer) :**
- contexte « réussir un geste technique » (exécution) : Technique (geste difficile), Dribbling (conduite serrée), Balance (au contact, roulette) ;
- contexte « tenter un geste technique » (décision) : Flair, Decisions ; « Tries Tricks » en penchant de fréquence (ticket 05), jamais de réussite ;
- défenseur : Anticipation, Positioning ; Agility par la physique.

**Lien avec l'existant :** complète le découpage de `v2-attributs-restants/07a` ; branche le geste préféré « Tries Tricks » (`v2-attributs-restants/05`).

**Blocked by:** 04f (ballon jouable entre deux touches), 04g (contournement), 04h (crochet), 04i (protection), 04o (état du défenseur, ajouté le 24/11/2026), `v2-attributs-contextes/01` et `02`.

**Bloque :** 04n.

**Status:** à faire (constantes et chiffres réels à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 60 min |
| Tests unitaires et comportementaux | 45 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 40** |

Confiance : faible. Hypothèses : chaque geste réutilise le décalage temporaire (04h) ou le ballon libre entre deux touches (04f) ; pas de rendu du geste au-delà d'un libellé à l'écran (`v2-mise-en-scene/05` pour l'animation). Au-dessus du seuil de 2 h : **découpage à examiner avant le code** (passement et double contact ; petit pont ; roulette).
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Scènes :** défenseur de face immobile à 1,5 m : petit pont tenté plus souvent à Flair 99, réussi plus souvent à Technique 99 ; perte plus fréquente qu'un contournement simple en cas d'échec ; « Tries Tricks » augmente la fréquence sans changer la réussite.
- **Statistiques (50 matchs) :** gestes par match et par type, réussite par type, pertes qui en résultent.

## Acceptance criteria

- [ ] Constantes produit, poids des contextes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Gestes tracés et affichés
- [ ] Effets des attributs probabilistes, jamais binaires ; contextes déclarés et documentés ; geste préféré en fréquence seulement ; pas de double comptage (R1)
- [ ] Scènes et mesure 50 matchs ci-dessus
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
