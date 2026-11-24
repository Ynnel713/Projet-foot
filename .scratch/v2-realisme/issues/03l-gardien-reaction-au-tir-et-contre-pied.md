# 03l: Gardien : anticiper le côté, être pris à contre-pied, rester figé sur un tir imparable

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, complément gardien, `docs/AUDIT_ROADMAP_V2.md` §13). **Priorité :** P1 (un gardien ne plonge pas sur tout : il devine, se fait prendre à contre-pied, ou regarde passer un ballon hors de portée). **Catégorie :** décision.

**Constat vérifié :** l'arrêt est une portée qui grandit après le temps de réaction, la même pour tous les tirs (`shooting.keeper_reach_m` : 1 m sans plonger, puis 3 m/s jusqu'à 2,8 m après 0,30 s ; `match._keeper_reaches`). Le gardien n'a aucune décision : il ne devine jamais un côté, il ne peut pas partir du mauvais côté, et rien ne distingue « il plonge et ne l'a pas » de « il ne bouge pas » ; la trace ne garde que l'écart et le temps de vol (`ShotEvent.keeper_gap_m`, `keeper_time_s`). 03f traite la vitesse du gardien au moment du tir (déjà lancé du mauvais côté), pas l'anticipation ni le refus de plonger.

**What to build:** Au départ du tir, le gardien peut anticiper un côté en lisant le tireur (orientation du corps 07a, pied, angle) : bonne lecture, portée vers ce côté plus grande ; mauvaise lecture, portée du côté opposé réduite (contre-pied). La tendance à partir tôt vient d'Eccentricity (tendance, jamais une qualité) et la justesse de la lecture d'Anticipation. Le gardien décide sur ce qu'il perçoit au départ du tir, jamais sur le point d'arrivée : il reste figé quand le ballon arrive avant la fin de sa réaction, quand il est pris à contre-pied ou masqué ; sinon il plonge vers le côté lu, même en vain. Sa réaction est tracée (plongeon, pas, figé, contre-pied) pour que l'écran la montre (`v2-mise-en-scene/05`) ; l'issue du tir reste celle de la portée.

**Ajout du 24/11/2026 (demande du propriétaire du 24/11/2026, éléments sur le gardien, point 2) : lecture, anticipation et réaction.**
- **Lecture selon la distance** : sur une frappe lointaine ou lisible, le gardien a le temps de lire la trajectoire (direction, hauteur du `05f`, effet du `14b`) et sa lecture est plus juste ; à bout portant, il est réduit au réflexe (Reflexes, `v2-attributs-restants/03b1`, existant), sans lecture.
- **Faux appel sur une feinte** : une feinte de frappe du tireur (`04k`) peut faire partir le gardien trop tôt ; une frappe placée à l'opposé devient alors bien plus difficile.
- **Vigilance (Concentration)** : en fin de match (fatigue) et juste après un but, un gardien peu concentré réagit un peu plus tard ; Concentration est un modulateur qui n'agit que dans sa condition, celle de la règle R3 de la carte (fatigue, après un but), sans toucher au temps de réaction de base (Reflexes) : constante à proposer avant le code. Ajouter la condition « peu sollicité depuis longtemps » demanderait de modifier la règle R3 : à proposer au propriétaire au lancement.
- **Pas de double comptage avec le `05i`** : ce ticket règle la lecture au départ du tir ; le `05i` règle la nouvelle réaction après une déviation.
- Visibilité masquée par un écran : `05k` (prévu).

**Attributs :** Anticipation (lecture du tireur, rayon existant : lire l'action) ; Eccentricity (tendance à partir tôt) ; Concentration (vigilance, modulateur R3, ajout du 24/11/2026).

**Lien avec l'existant :** 05b (arrêt par portée, livré) ; 03f (appuis au moment du tir) ; 15c (tête : la tête croisée à bout portant est le cas typique) ; `v2-attributs-restants/02a` (le penalty réutilise la même anticipation).

**Blocked by:** 03f, 07a ; `v2-attributs-restants/03b1` (03b découpé le 22/11/2026 : seul l'arrêt, 03b1, est un prérequis). Volets du 24/11/2026 dépendants : faux appel sur une feinte après `04k`, lecture de la hauteur après `05f`, de l'effet après `14b` ; chacun est fait seulement si son ticket est livré, sinon reporté (noté au lancement).

**Bloque :** `v2-mise-en-scene/05` ; `v2-attributs-restants/10b` (piqué sur un gardien parti tôt).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** (lecture et contre-pied) ; **2 h 45** avec les volets du 24/11/2026 (lecture selon la distance, vigilance, faux appel) : découpage à faire au lancement |

Confiance : moyenne. Hypothèses : la lecture du tireur est un tirage dont la justesse dépend d'Anticipation ; une seule constante de gain et de perte de portée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir à 6 m en lucarne opposée (vol plus court que sa réaction) : gardien figé, but ; lucarne à 20 m : plongeon en vain ; tir sur le gardien : arrêt
- **Comportementaux (profils comparés) :** Anticipation 99 contre 40 : part des contre-pieds ; Eccentricity haute : plus de départs anticipés, plus de contre-pieds et plus d'arrêts spectaculaires
- **Statistiques (séries de matchs) :** 50 matchs : buts encaissés sans plongeon, contre-pieds, arrêts sur anticipation

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Réaction du gardien tracée sur chaque tir cadré (plongeon, pas, figé, contre-pied)
- [ ] Le gardien reste figé seulement si le ballon arrive avant sa réaction, s'il est pris à contre-pied ou masqué ; sinon il plonge, même en vain ; un contre-pied réduit l'arrêt dans le bon sens
- [ ] Taux d'arrêt global mesuré avant et après (aucun réglage pour le ramener)
- [ ] Volets du 24/11/2026 : scène A/B Concentration 99 contre 11 en fin de match (réaction plus tardive à 11, aucun écart hors de la condition) ; lecture plus juste sur une frappe lointaine que sur une frappe à bout portant ; faux appel sur une feinte (si `04k` livré)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
