# 06b: Application de l'import de la sauvegarde FM au classeur

**Status:** livré (23/11/2026), validé expert + QC

**Blocked by:** 06a (livré)

**What to build:** lancer `scripts/import_fmsave_attributes.py --write` sur `data/joueurs.xlsx`, puis `scripts/compute_moyenne_fm.py` et `scripts/generate_national_teams.py` ; vérifier le classeur et mesurer l'effet sur les moteurs. Aucun code modifié ; seules les données changent.

**Décision du propriétaire (23/11/2026) :** « peux tu remplir la base de données ? » ; règles d'import : ticket 06a.

**Estimation (travail effectif) :** analyse 15 min, application et recalculs 20 min, tests 20 min, vérifications et mesures 30 min ; total 1 h 25 ; confiance moyenne (des tests peuvent dépendre de valeurs du classeur). Temps machine hors total : suite complète, calibration V1 (2 × 50 saisons × 2 championnats), mesure V2 (2 × 20 matchs).

## Critères d'acceptation
- [x] Classeur : même nombre de lignes et mêmes ID ; colonnes modifiées limitées aux attributs, Pieds, Weak foot (/5), Taille FM (cm) (import), Moyenne FM (recalcul) et onglets des sélections (régénération) ; tableau `Tableau8` et feuilles intacts.
- [x] Moyenne FM recalculée pour tous ; aucune ligne sans Moyenne FM ; chargeur V1 sans erreur (9 championnats, vivier perso).
- [x] Mesure avant/après publiée ici : Moyenne FM (distribution, plus fortes variations), note des clubs, calibration V1 (Ligue 1, Premier League), indicateurs V2 (20 matchs, graine fixée).
- [x] Déterminisme : relancer l'import sur le classeur écrit ne change plus rien (0 cellule).
- [x] Suite complète passée (tests adaptés si une valeur du classeur était figée, avec justification).

## Journal

23/11/2026 — implémenté (données seules, aucun code modifié).
- Commandes : `import_fmsave_attributes.py --write`, `compute_moyenne_fm.py`, `generate_national_teams.py` (copies de secours `joueurs_backup_*.xlsx` supprimées : non suivies, la version précédente est dans git).
- Import : 2 331 joueurs retrouvés, 2 226 modifiés (dont 20 sans attribut auparavant) ; 22 337 cellules d'attributs, Pieds 671, Weak foot 185, Taille FM 20.
- Contrôle du classeur (avant / après, cellule par cellule) : mêmes feuilles, 7 474 lignes et 69 colonnes, mêmes ID dans le même ordre, `Tableau8` A1:BQ7474 inchangé. Colonnes modifiées dans « Infos principales » : attributs, Pieds, Weak foot (/5), Taille FM (cm), Moyenne FM (4 567 joueurs) ; onglets régénérés : Europe 1 416, Afrique 849, Amérique 618, Asie 262, Océanie 83 cellules. Aucune autre feuille touchée.
- Idempotence : relancer l'import sur le classeur écrit -> 0 joueur, 0 cellule.
- Moyenne FM : 4 567 joueurs changent (recalage par rangs : l'import déplace aussi le rang des autres joueurs de la même famille) ; écart moyen + 0,03, |écart| moyen 1,68 parmi ceux qui changent ; 342 à ±5 points ou plus, 112 à ±10 ou plus ; 0 ligne sans Moyenne FM. Plus fortes hausses : Kieran Morrison (Sheffield Wednesday, 19 ans) 20 -> 62.5 ; Guy-Noël Zohouri (Le Havre AC, 19 ans) 19.5 -> 51.5 ; Bénito (CF Estrela Amadora, 23 ans) 37 -> 68 ; Ceadach O'Neill (Arsenal FC U21, 18 ans) 20 -> 50.5 ; Lassine Diarra (Olympique Lyon, 23 ans) 21.5 -> 50.5. Plus fortes baisses : Bruno Ecuele Manga (Sans club, 38 ans) 53 -> 35 ; Mezian Mesloub (RC Lens, 16 ans) 69 -> 52.5 ; Damián Bobadilla (São Paulo FC, 25 ans) 74 -> 61 ; Christos Mouzakitis (Hull City, 19 ans) 73 -> 60.5 ; Aaron Ramsdale (Southampton FC, 28 ans) 77.5 -> 66. 315 joueurs sans attributs gardent leur Moyenne joueur (335 avant).
- Sélections nationales : 129 pays, 91 complets (18/18) avant comme après ; mêmes 6 nationalités ignorées avant comme après (Afghanistan, Barbados, Latvia, Namibia, St. Lucia, Uganda).
- V1, calibration à graine fixée (`random` et `numpy.random` à 20261123, lanceur hors dépôt ; le script seul n'est pas reproductible), 50 saisons :
  - Ligue 1 : note moyenne des clubs + 0,32 ; Monaco 74,3 -> 76,5 (rang moyen 6,34 -> 3,94), Auxerre 68,3 -> 66,3 (9,74 -> 11,84) ; buts par match 3,01 -> 3,06 ; domicile / nul / extérieur 47,1 / 21,1 / 31,8 -> 47,5 / 20,5 / 32,0 %.
  - Premier League : note moyenne + 0,05, aucun club à plus de ± 1,0 ; buts par match 2,92 -> 2,91.
- V2, `measure_v2 20` (graines AUDIT_SEED + k), Ligue 1 : buts par match 4,05 -> 4,85 ; tirs par équipe 14,3 -> 14,0 ; passes réussies 84,5 -> 84,3 % ; part des tirs de près 66,4 -> 66,6 %. Attributs clés des titulaires potentiels (moyenne par poste et championnat) : variations < 1 point (ex. Ligue 1, attaquants Finishing 59,4 -> 60,1 ; gardiens Reflexes 67,2 -> 67,0). L'écart de buts (0,8) vaut environ 1,2 écart-type de la différence de deux séries de 20 matchs (≈ 0,65) : non démontré, à confirmer sur une série plus longue si besoin (point de vigilance).
- Suite complète sur le classeur écrit : 3 543 passés, 14 désélectionnés (13 min 58), aucun test adapté.

## Comments

23/11/2026 — expert : APPROVED (empreinte ade2f9a1). QC : VALIDÉ. Clôture journalisée : VALIDÉ.
- Remarques facultatives : plus fortes variations de Moyenne FM nommées dans le journal (A1, fait) ; buts V2 à confirmer sur au moins 60 matchs par configuration si une calibration V2 s'appuie sur ce classeur (A2, point de vigilance) ; compte attendu de `CLAUDE.md` (3 452) périmé, 3 543 depuis le 06a (A3, hors périmètre, à faire par un ticket documentaire avec l'accord du propriétaire).
- Durée : estimée 85 min, réelle environ 70 min (− 18 %) : analyse 15, application et recalculs 10, tests 15, vérifications et mesures 30. Temps machine hors total : deux mesures V2 de 20 matchs (45 min chacune), quatre calibrations V1 de 50 saisons, comparaison cellule par cellule (≈ 3 min), suite complète (14 min).
