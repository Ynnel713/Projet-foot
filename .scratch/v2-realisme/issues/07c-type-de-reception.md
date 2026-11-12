# 07c: Réception de face, de profil ou dos au jeu

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** perception.

**Constat vérifié :** la réception ne tient compte que de la vitesse du ballon et de la pression (`possession.control_difficulty`) ; pendant la réception le joueur avance toujours vers le but adverse (`cerveau.py:151-153`).

**What to build:** Classer chaque réception selon le cap du receveur, la direction d'arrivée du ballon et la direction du but adverse : de face, de profil (ouvert), dos au jeu. Le type est tracé ; le receveur qui a le temps se met de profil avant l'arrivée du ballon (rotation du 07a).

**Hors de ce ticket :** effet sur le temps de contrôle (07d).

**Attributs :** aucun

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 04i, 07d, 07g, 08c, `v2-collectif/31`.

**Status:** livré (12/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : seuils d'angle : valeurs proposées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** trois scènes (ballon venant de derrière, de côté, de face) : trois types attendus
- **Statistiques (séries de matchs) :** 20 matchs : répartition des types par poste

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code : de face sous 60°, de profil de 60 à 120°, dos au jeu au-delà (angle cap / but adverse) ; préparation du receveur visé à mi-chemin entre le ballon et le but (course rapide prioritaire, règle du 07a) ; valeur réelle non trouvée (validé le 12/11/2026, « ok ») ; puis receveur marqué (adversaire à moins de 2 m, `possession.MARKED_RADIUS_M`) qui ne s'ouvre pas (validé le 12/11/2026, « ok »)
- [x] Type de réception tracé : `MatchTrace.receptions` (`ReceptionEvent` : minute, équipe, joueur, poste, type, contrôle réussi, façon de recevoir), au premier contact d'une passe par un coéquipier ; hors du journal des événements (chaînes de causes du 19b inchangées)
- [x] Répartition par poste rapportée (20 matchs, 17 544 réceptions, `07c-repartition.txt`) : de face 76,0 %, de profil 22,9 %, dos au jeu 1,1 % ; BU 45,5 / 52,7 / 1,7 % ; DC 93,8 / 5,4 / 0,9 % (voir Comments : peu de dos au jeu, cause hors du ticket)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes (jeu et cap) sur deux exécutions ; jeu identique avant / après sur 20 matchs (44 buts, 694 tirs) (`07c-empreintes.txt`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 778 passés, 14 désélectionnés (2 773 au 07f + 5), 7 min 29 (`07c-suite.txt`)

## Comments

**12/11/2026, implémentation.**
- `orientation.reception_type` (secteurs 60 / 120°) ; `orientation.desired_facing(..., goal=)` : le receveur visé d'une passe en vol (non marqué au départ) vise la bissectrice ballon / but (`_open_body`), sauf en course rapide ; ballon exactement opposé au but : perpendiculaire la plus proche de son cap. Il n'y arrive avant le ballon que si sa rotation (Agility, 07f) le permet.
- `match._marked` : receveur marqué au départ de la passe (`ball.receiver_marked`, posé aux deux endroits où le receveur est désigné : passe de jeu et remise en jeu). Jugé une fois par passe : relu à chaque pas, le seuil de 2 m faisait basculer le cap (90 → 126 → 162 → 90°) quand l'écart au marqueur oscillait autour de 2 m (scène de diagnostic).
- `possession._MARKED_RADIUS_M` rendu public (`MARKED_RADIUS_M`), lu par `match` (import par l'API publique) ; commentaire de `tests/test_v2engine_pressing.py` aligné (nom et valeur 2 m).
- Tests : `tests/test_v2engine_reception.py`, 5 tests (secteurs, direction d'ouverture, trois scènes de profil / de face / dos au jeu, receveur marqué à 1,5 m dos au jeu et à 3 m de profil, `_marked`) ; sans la règle d'ouverture, la scène de derrière donne dos au jeu et celle de côté de profil (discriminante).

**12/11/2026, répartition et décision du propriétaire.** Première version : dos au jeu 0,9 % (BU 0,9 %). Condition du receveur marqué ajoutée (« ok ») : dos au jeu 1,1 % (BU 1,7 %). Cause mesurée (4 matchs, 4 100 passes) : 1,2 % des passes partent vers un receveur marqué à moins de 2 m (BU 2,7 %, DC 0 %) et 86 % des receveurs n'ont aucun adversaire à moins de 5 m : le passeur évite les receveurs marqués et la défense colle peu. Ce n'est pas un réglage du 07c : clôture avec réserve (« ok »), répartition à remesurer au 10g et avant le 07d (critère ajouté aux deux tickets). Estimation révisée et annoncée : 2 h 45.

**12/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS (`07c-expert-1.md`, hors dépôt). QC : VALIDÉ. Clôture : VALIDÉ. Réserve acceptée par le propriétaire (« ok », clôture avec réserve) :
- A1 [réserve] : dos au jeu 1,1 % (BU 1,7 %), faute de passes vers des receveurs marqués ; répartition à remesurer au 10g et avant le 07d (critère inscrit dans les deux tickets).
- A2 [facultatif] : ballon presque à l'opposé du but, le côté de l'ouverture peut alterner si le receveur dérive en travers ; correctif possible : perpendiculaire la plus proche du cap au-delà d'environ 165°.
- QC, non bloquant : scène « ballon de face » vérifiée au niveau de `desired_facing` seulement ; lignes vides en trop dans le test.

**Durée.** Estimée 1 h 50, révisée et annoncée à 2 h 45. Réelle environ 2 h 50, non chronométrée (analyse 30 min, développement 50 min, tests 40 min, intégration et vérifications 50 min) : + 55 % sur l'estimation d'origine, + 3 % sur la révision. Causes : condition du receveur marqué ajoutée après la première répartition, puis jugée au départ de la passe (bascule du cap autour du seuil) ; seconde série de mesures ; cause du peu de dos au jeu mesurée. Temps machine hors total : 5 séries de 20 matchs, mesure de 4 matchs, suite complète deux fois (7 min 33 et 7 min 29).

