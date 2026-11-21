# 18l: Recalibration des volumes après la ligne avec ballon

**Chantier :** `v2-realisme` (suite du ticket 09j, décision du propriétaire du 16/11/2026 : « Clôturer + ticket suivi »). **Priorité :** P1. **Catégorie :** mesure.

**Constat (16/11/2026, série de 20 matchs, `scripts/bench_series`, indicatif) :** le calage de la dernière ligne avec ballon (09j) remonte tout le bloc qui attaque (centraux à 37 m de leur but au lieu de 19 m, ballon entre 40 et 55 m), comme voulu, mais déplace les volumes :

| Par match | Avant 09j | Après 09j | Repère réel (ordre de grandeur, non vérifié dans une source) |
|---|---|---|---|
| Buts | 4,35 | 6,8 | environ 2,7 |
| Hors-jeu | 0,7 | 4,1 | environ 4 |
| xG neutre / après frappe | 5,0 / 4,5 | 6,5 / 6,6 | |
| Tirs par équipe | 21,0 | 22,2 | |
| Tirs de près (16 m) par équipe | 4,8 | 7,3 | |
| Tirs après récupération dans le camp adverse | 24,5 | 12,8 | |
| Passes | 1 089 | 1 280 | |
| Pertes de balle | 215 | 259 | |

Ballon dans son propre tiers (10 à 25 m) : centraux à peine plus bas avec ballon que sans (18,4 contre 18,9 m) ; relève du placement de construction (25b).

**What to build :** d'abord chercher d'où viennent les buts en plus (tirs de près, contres dans le dos de la ligne haute, gardien, défense préventive absente : 09g), sur une série d'au moins 50 matchs, après 09e et 25b qui changent encore le bloc. Puis proposer au propriétaire la correction (constantes ou ticket de comportement) ; aucune constante changée sans son accord.

**Attributs :** aucun nouveau.

**Blocked by:** `v2-realisme/09e`, `v2-realisme/25b` (le bloc avec ballon change encore) ; `v2-realisme/09g` (défense préventive) à planifier avant ou pendant ce ticket (réserve A3 du 09j, acceptée par le propriétaire le 16/11/2026). Reprend aussi la réserve A2 du 09j : centraux à vérifier dans le tiers défensif avec ballon.

**Bloque :** 18m (ajouté le 21/11/2026).

**Status:** livré (21/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement (diagnostic) | 30 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications (séries avant et après) | 45 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible (la cause n'est pas connue). Temps machine, non compté : séries de 50 matchs avant et après (environ 40 min chacune sur 4 cœurs).

## Acceptance criteria

- [x] Origine des buts en plus décomposée (situations, distances, origines des tirs) sur 50 matchs au moins
- [x] Correction proposée au propriétaire et validée avant le code
- [x] Buts, xG, tirs, hors-jeu, passes rapportés (état du moteur ; « après » reporté au 18m, aucune constante changée ici sur décision du propriétaire)
- [x] Durée réelle relevée et comparée à l'estimation

## Comments

**Diagnostic (21/11/2026, `docs/INDICATEURS_V2.md` section 56).** Script en lecture seule `.scratch/v2-realisme/mesures/18l-diag.py` (tirs de `MatchTrace.shots`, origine des buts par `scripts.v2_chain`), données `18l-diag-50.json` (50 matchs, graines du banc), synthèse `18l-diag-synthese.py` → `18l-diag-50-synthese.txt`. Totaux identiques au banc du 28a (20,55 tirs par équipe, 5,06 buts par match ; hors-jeu 3,74, passes 1 270, xG neutre 4,88 par match) ; match 0 identique sur deux exécutions.

**Résultat.** Excès d'environ + 2,3 buts par match au-dessus du repère moyen, dont environ + 1,6 par les frappes de loin : 12,86 tirs hors surface par équipe (62,6 %) contre environ 4,1 (31,7 %), 1,92 but par match hors surface (38 %) contre environ 0,3 (11,7 %). Conversion dans la surface trop haute (20,4 % contre 14,7 %). Modèle de chance de but conforme par distance : la décision et les situations sont en cause, pas la formule. 62 % des tirs suivent une conduite ; 0,04 tir par équipe sur centre ; 63,6 % des buts partent d'une récupération (interception 54,2 %) ; saut principal au 09j.

**Correction proposée et validée par le propriétaire (21/11/2026, « ok avec tes propositions ») :** (1) ticket `18m`, sélection des frappes de loin ; (2) `10f`, `10g` avancés (défense de la surface) ; (3) ce ticket clos comme diagnostic, aucune constante changée. Remarque du propriétaire (« le jeu était très axial […] très peu de centres, dédoublement de latéraux ») : ticket `25i` ajouté (dédoublement du latéral, orphelin depuis `v2-collectif/14`).

**Réserves du 09j reprises.** A2 (centraux dans le tiers défensif avec ballon) : non revérifiée ici, relève du placement de construction (`25b`, livré) ; A3 (`09g`, défense préventive) : toujours à faire, à planifier avant le 18m si ses mesures montrent des buts encaissés en transition.

**Clôture (21/11/2026).** Expert : **APPROVED** (empreinte `7bc71f30…`, FICHIERS : les deux scripts de diagnostic). QC : **VALIDÉ**. Clôture journalisée : VALIDÉ. Points facultatifs de l'expert : A1 (la tranche 16,5-25 m contient des tirs en angle dans la surface) et A2 (excès de frappes de loin déjà relevé au 18e) reportés dans la section 56 et dans le 18m ; A3 (critère avant / après reformulé) couvert par la décision du propriétaire.

**Durée.** Estimée 2 h (30 / 30 / 15 / 45 min) ; réelle environ 55 min (analyse 20, diagnostic 15, vérifications 5, intégration et documentation 15), hors temps machine (série de 50 matchs, environ 30 min) : − 54 %. Cause : le banc du 28a, aux mêmes graines, et l'outil d'origine des buts (`scripts/v2_chain.py`) existaient déjà, un seul script de lecture a suffi ; la correction, prévue dans l'estimation (séries avant et après), est reportée au 18m sur décision du propriétaire.
