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

**Status:** à faire (constantes à proposer avant le code)

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

- [ ] Constante validée par le propriétaire avant le code
- [ ] Scène : porteur à 20 m dans l'axe, coéquipier libre dans la surface : il ne frappe plus ; sans option meilleure, il frappe encore
- [ ] Tirs hors surface : de 12,86 à 5 par équipe au plus ; part des buts hors surface : de 38 % à 15 % au plus (cibles indicatives, à confirmer)
- [ ] Buts, tirs, xG, conversion dans et hors surface, pertes de balle rapportés avant et après (50 matchs appariés, intervalles)
- [ ] Profil Long Shots toujours dans le bon sens
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
