# 15c: Qualité de la tête : Heading

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (gagner le duel ne suffit pas à bien jouer le ballon). **Catégorie :** exécution.

**Constat vérifié :** voir 15b.

**What to build:** Le vainqueur du duel joue le ballon de la tête (tir, passe, dégagement) avec une précision et une puissance réglées par Heading ; la tête au but passe par la résolution physique du tir (05a).

**Attributs :** Heading

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/01` : tête.

**Blocked by:** 15b (Duel aérien : taille, Jumping Reach, Strength au contact); 05a (Tir : le ballon part vers son point d'arrivée, le but n'est plus tiré au départ).

**Bloque :** 15d, 15f.

**Status:** découpé (chapeau, 24/11/2026) en `15c1` (choix du geste de la tête), `15c2` (physique de la tête), `15c3` (tête au but), `15c4` (remise et passe de la tête) ; dégagement : `15d` (existant). Découpe validée par le propriétaire le 24/11/2026 (« Oui, dans cet ordre ») ; fatigue : prise via les notes (tickets 20), pas de lecture propre (choix du propriétaire du 24/11/2026)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : tête au but : vitesse plus faible qu'un tir du pied.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Comportementaux (profils comparés) :** Heading 99 contre 11 : têtes cadrées plus souvent

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet de Heading mesuré en scène A/B
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
- 24/11/2026 : périmètre élargi par le propriétaire (« la qualité doit dépendre de l'état du joueur au contact (en l'air vs pied au sol, équilibre, bousculade, fatigue, élan), de son orientation/posture, de la hauteur d'impact et des caractéristiques du ballon entrant (vitesse, angle) [...] coupler les notes pertinentes (tête, décision, finition, passe, sang-froid, vision) aux quatre gestes possibles : remise/passe, tir, dégagement défensif et amorti/contrôle [...] trajectoire, vitesse et dispersion (angle et dosage) cohérentes avec l'évaluation tactique [...] cas limites (hors-jeu, ligne de but, dégagements courts dans l'axe) »), environ 8 h : découpé.
- Constat vérifié (24/11/2026) : un ballon joué de la tête est aujourd'hui un contrôle (`possession.attempt_control`, First Touch), posé au pied (`match._step_loose_ball`), puis une décision au sol ; Heading n'est lu nulle part ; pas de dégagement.
