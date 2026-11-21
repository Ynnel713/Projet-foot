# 18m: Sélection des frappes de loin

**Chantier :** `v2-realisme` (diagnostic du `18l`, correction validée par le propriétaire le 21/11/2026 : « ok avec tes propositions »). **Priorité :** P1 (premier contributeur de l'excès de buts). **Catégorie :** décision.

**Constat vérifié (18l, 50 matchs, `docs/INDICATEURS_V2.md` section 56) :** 12,86 tirs hors surface par équipe (62,6 % des tirs) contre environ 4,1 (31,7 %, Opta R1) ; 13,23 tirs par équipe entre 16,5 et 25 m ; 1,92 but par match hors surface (38 % des buts) contre environ 0,3 (11,7 %, R3) ; 62 % des tirs suivent une conduite. Le modèle de chance de but est conforme par distance (`shooting.base_chance`) : le défaut est la **décision**. Au centre à 20 m, la chance de base d'un tir (0,059) dépasse la valeur de garder le ballon (`danger.danger`, 0,051) ; la valeur d'un tir manqué (`decision.shot_value`, ticket 18k) ne suffit pas à l'inverser, et les passes vers la surface sont peu envisagées (portée de Vision, `30a`).

**What to build:** Hors de la surface, le porteur ne frappe que si la frappe vaut nettement mieux que la meilleure option pour continuer l'action (passe, conduite) ; le seuil se lit sur les valeurs existantes de la monnaie commune (`decision.option_value`, `shot_value`), sans nouvelle pénalité arbitraire. Long Shots garde son rôle (exécution) ; Decisions (choisir) et le goût du risque (Flair, `v2-attributs-contextes/05`) restent séparés selon la carte des attributs (ADR 0002).

**Hors de ce ticket :** le modèle de chance de but (conforme) ; la défense de la surface (`10f`, `10g`) ; la portée de Vision (`30b`).

**Attributs :** Decisions (rayon existant) ; aucun nouvel effet sans vérification de la carte (`docs/CARTE_ATTRIBUTS_V2.md`).

**Constantes à proposer avant le code :** marge de la frappe sur la meilleure option hors surface (forme : écart de valeur, ou rapport). Chiffres réels : R1 à R3 (31,7 % des tirs hors surface, 4,2 % de conversion, 11,7 % des buts hors surface).

**Points de l'expert au 18l (21/11/2026) :** croiser surface et distance (ou angle) dans la mesure, la tranche 16,5-25 m contenant des tirs en angle dans la surface ; ne pas chercher la cause dans le seul 09j (excès de frappes de loin déjà relevé au 18e) ; vérifier que moins de frappes de loin n'augmente ni les pertes ni les buts encaissés en transition (`09g` encore à faire).

**Lien avec l'existant :** à coordonner avec `30b` (voir le joueur libre), qui donnera plus d'options à la place de la frappe.

**Blocked by:** 18l.

**Bloque :** `v2-collectif/22c` (calibration des tirs et des buts).

**Status:** livré (21/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs appariés, profil Long Shots) | 30 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : une seule règle dans `decision.choose_action` (comparaison des valeurs déjà calculées) ; le diagnostic du 18l (`.scratch/v2-realisme/mesures/18l-diag.py`) sert de mesure avant / après.
Temps machine, non compté : suite complète ; série appariée de 50 matchs ; diagnostic du 18l relancé.

## Acceptance criteria

- [x] Constante validée par le propriétaire avant le code (0,03 le 21/11/2026, puis 0,05 après la série : « Ok pour 0,05 »)
- [x] Scène : porteur à 20 m dans l'axe, coéquipier libre dans la surface : il ne frappe plus ; sans option meilleure, il frappe encore
- [ ] Tirs hors surface : de 12,86 à 5 par équipe au plus ; part des buts hors surface : de 38 % à 15 % au plus (cibles indicatives, à confirmer) — **partiel** : tirs 4,59 (atteint), part des buts 25,1 % (non atteint, conversion hors surface 13,3 %, voir Comments)
- [x] Buts, tirs, xG, conversion dans et hors surface, pertes de balle rapportés avant et après (50 matchs appariés, intervalles)
- [x] Profil Long Shots toujours dans le bon sens
- [x] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**Implémentation (21/11/2026).** `decision.LONG_SHOT_MARGIN = 0,05` ; dans `choose_action`, hors de la surface (`geometry.in_penalty_area`) et hors coup de pied arrêté, la valeur perçue de la frappe est diminuée de la marge avant la comparaison, et le meilleur choix factuel (`best`, `best_kind`, `gap`, échelle de l'erreur de perception) se juge avec la même règle, pour que respecter la règle ne compte pas comme une erreur de Decisions (écart à la proposition initiale, signalé au propriétaire). `evaluate_options`, `shot_value` et l'exécution (Long Shots) inchangés. Marge nulle : moteur identique à l'avant (vérifié sur 50 matchs, totaux du 18l). Tests : `tests/test_v2engine_frappes_de_loin.py` (6 : valeur, passe vers le libre au lieu de la frappe à 20 m, frappe gardée sans meilleure option, pas de marge dans la surface ni sur coup franc, part des frappes sous perception brouillée 54 % → 19 %).

**Mesures (`docs/INDICATEURS_V2.md` section 57, scripts et données dans `.scratch/v2-realisme/mesures/18m-*`).** Premier essai à 0,03 : 7,04 tirs hors surface par équipe, cible manquée ; 0,05 retenu par le propriétaire. À 0,05 : tirs hors surface 12,86 → **4,59** par équipe (− 8,27 ± 0,87 ; part 62,6 % → 28,9 %, réel 31,7 %) ; buts hors surface 1,92 → 1,22 par match (part 37,9 % → **25,1 %**, cible 15 % non atteinte) ; buts 5,06 → 4,86 (− 0,20 ± 0,96, non significatif) ; tirs dans la surface + 3,59 ± 0,91 ; passes + 70 ± 22, pertes + 12 ± 7 ; buts sur récupération en 15 s ou moins 0,90 → 1,00. Profil Long Shots : part des 70 et plus parmi les frappes de loin 22 % → 36 %.

**Écart restant.** Les frappes de loin gardées convertissent à 13,3 % (réel 4,2 %) : situations de frappe trop faciles (ligne de tir et tireur libres à 20 m), et les frappes perdues deviennent des tirs dans la surface convertis au-dessus du réel. Relève de la défense de la surface et de ses abords (`10f`, `10g`) et de la défense préventive (`09g`), pas d'une marge plus forte (la décision suit déjà la valeur).

**Vérifications.** Suite complète : 3 458 passés, 0 ignoré, 14 désélectionnés (attendu 3 452 + 6 tests ajoutés). Déterminisme : match 0 du banc, deux exécutions, même empreinte (2-1, 26 tirs, `2340924cab3f897b`) ; marge nulle identique au moteur d'avant (totaux du 18l sur 50 matchs). V1 non touchée.

**Durée.** Estimée 2 h (20 / 40 / 30 / 30 min) ; réelle environ 2 h 15 (analyse et mesure préalable 30, développement 25, tests 30, intégration, deux séries et documentation 50), hors temps machine (8 matchs, trois séries de 50 matchs, suite complète de 13 min) : + 13 %.

**Clôture (21/11/2026).** Expert : **APPROVED_WITH_RESERVATIONS** (empreinte `07178306…`, FICHIERS : `v2engine/decision.py`, `tests/test_v2engine_frappes_de_loin.py`, scripts `18m-marges.py`, `18m-serie.py`, `18m-synthese.py`). QC : **VALIDÉ** (même réserve). Clôture journalisée : VALIDÉ.
- A1 (réserve) : critère 3 partiel, part des buts hors surface 25,1 % pour 15 % visés et buts non significativement en baisse ; correction reportée à `10f`, `10g`, `09g`, `22c` avec les conversions mesurées (13,3 % hors surface, 16,1 % dans la surface). Acceptée par le propriétaire : « Jaccepte A1 ». Reportée dans les quatre tickets.
- A2 (facultatif) : erreur de perception calculée sur la valeur de choix (plus étroite quand la meilleure option est une frappe de loin, cas devenus rares) ; à revoir si la courbe de Decisions bouge.
- A3 (facultatif) : buts sur récupération rapide sans intervalle ; reporté au `09g`.
- A4 (facultatif) : `docs/INDICATEURS_V2.md` hors FICHIERS, suivi documentaire.
- À surveiller (expert) : conversion hors surface non croissante avec Long Shots (effectifs faibles, au `22c`) ; après `30b`, ne pas descendre nettement sous 31,7 % de tirs hors surface.
