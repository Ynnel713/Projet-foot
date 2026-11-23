# 06a: Import des attributs d'une sauvegarde FM (script et essai à blanc)

**Status:** livré (23/11/2026), validé expert + QC

**Blocked by:** —

**What to build:** `scripts/import_fmsave_attributes.py`. Source : `data/fmsave-list.csv`, export d'une sauvegarde Football Manager fourni par le propriétaire (15 094 joueurs et joueuses, 47 attributs, pieds gauche/droit sur 20, taille ; pas de nationalité ni de sexe). Le script retrouve dans cette source les joueurs **déjà présents** dans `data/joueurs.xlsx` et met à jour leurs données ; il n'ajoute aucun joueur. Essai à blanc par défaut (rapport seulement), écriture avec `--write` (ticket 06b).

**Décisions du propriétaire (23/11/2026) :**
- « N'ajoute pas de nouveaux joueurs aux clubs présents dans la base. Tout ce que je souhaite c'est récupérer les données attributs de ces joueurs. » Les joueuses n'entrent donc jamais dans la base (seuls des joueurs déjà présents sont mis à jour).
- Attributs : **remplacés** par ceux de la sauvegarde pour tous les joueurs retrouvés, en gardant le jeu habituel de 36 attributs (joueur de champ : sans les 11 attributs de gardien ; gardien : sans les 11 attributs propres au jeu de champ). Joueur retrouvé sans aucun attribut : reçoit le jeu de son métier (poste principal).
- Pied fort (« Pieds ») : la sauvegarde fait foi pour tous les joueurs retrouvés (D si pied droit > gauche, G si gauche > droit ; égalité : valeur actuelle gardée, rien d'inventé).
- Weak foot (/5) : recalculé depuis le moins bon pied (1-20), échelle observée dans la base : 1-4 → 1, 5-8 → 2, 9-12 → 3, 13-20 → 4.
- Taille FM (cm) : remplie seulement si vide. Rien d'autre n'est modifié (« Rien d'autre »).
- Échelle (« pense à harmoniser toutes les données ») : la sauvegarde note de 1 à 20, le classeur de 5 à 99. Mesure : 99,6 % des valeurs du classeur sont des multiples de 5 ; pour chaque valeur v de la sauvegarde, la médiane du classeur vaut v × 5 (20 -> 99). Conversion appliquée : v × 5, 20 -> 99. Après conversion, sur les joueurs communs : 74 % des valeurs identiques, 90 % à un cran (5 points), écart moyen + 0,6.
- Incertitudes (« s'il y a des incertitudes concernant des homonymes aide toi de transfermarkt avec la donnée club ») : départage par le club (même club malgré deux écritures), puis, à défaut, par la valeur marchande du classeur (issue de Transfermarkt) à moins d'un facteur 3 de celle de la sauvegarde. Aucun accès au site Transfermarkt : la donnée Transfermarkt utilisée est celle déjà dans le classeur.

**Estimation (travail effectif) :** analyse 20 min, développement 45 min, tests 30 min, vérifications 15 min ; total 1 h 50 ; confiance moyenne (correspondance par nom et âge sans nationalité ni date de naissance dans la base).

## Mesures préalables (23/11/2026, classeur actuel)
- Jeux d'attributs : 6 290 joueurs de champ et 848 gardiens à 36 attributs ; 335 joueurs sans attribut.
- Correspondance nom normalisé + âge à ±1 an, unique : 2 335 joueurs retrouvés (21 des 335 sans attribut), 3 homonymes écartés.
- Accord avec la base sur les joueurs communs : taille identique pour 89 % ; weak foot selon l'échelle ci-dessus ≈ 93 % ; pied fort en désaccord pour 8 % des 2 922 renseignés.

## Critères d'acceptation
- [x] Correspondance : nom normalisé identique et âge à ±1 an ; refus si un seul des deux est gardien, ou si aucun poste de la sauvegarde n'est à 2 crans ou moins d'un poste du classeur (`players.poste_distance`) ; homonymes et conflits (une ligne pour plusieurs joueurs) départagés par le club puis par la valeur marchande, sinon écartés.
- [x] Aucune ligne ajoutée ni supprimée au classeur ; seules les colonnes Attributs (jeu du métier), Pieds, Weak foot (/5) et Taille FM (cm) peuvent changer.
- [x] Jeu de 36 attributs respecté pour chaque joueur mis à jour (aucun attribut de l'autre métier écrit).
- [x] Essai à blanc par défaut : classeur intact ; rapport CSV par joueur (statut, club base / sauvegarde, attributs changés, pieds, weak foot, taille) et bilan imprimé.
- [x] Tests hors ligne ; suite complète passée (3 543 passés = 3 532 + 11, 14 désélectionnés, 12 min 57).

## Journal

23/11/2026 — implémenté.
- `scripts/import_fmsave_attributes.py` (nouveau), source `data/fmsave-list.csv` (copie de l'export fourni), rapport `data/fmsave_import_report.csv` (non suivi, regénéré à chaque exécution, identique d'une exécution à l'autre).
- Essai à blanc sur le classeur réel : 2 331 joueurs retrouvés (dont 20 sans aucun attribut), 5 conflits restants (homonymes de la base absents de la sauvegarde : Vitinha du Genoa, André Silva de São Paulo, Mamadou Coulibaly d'Al-Jazira, Mohamed Kaba de Gil Vicente, Paulinho d'Académico de Viseu), 2 postes incompatibles (Mohamed Touré : BU / DC homonyme ; Ayman Yahya : LB / AMR, 3 crans). 2 226 joueurs modifiés ; Pieds 671, Weak foot 185, Taille FM 20 (dernière exécution) ; classeur intact (même empreinte avant et après).
- Défauts trouvés par la mesure et corrigés avant revue : échelle 1-20 / 5-99 (sans conversion, 83 682 cellules auraient été divisées par cinq) ; contrôle par famille de poste trop strict (32 vrais joueurs écartés, ex. Lewis-Skelly LB / DM MC), remplacé par la distance de poste.
- Départages : 3 homonymes et 4 conflits par le club, 1 conflit (Paulinho « SEP » 12,3 M€ -> Palmeiras 9 M€, pas Viseu 0,3 M€) par la valeur marchande.
- Tests : 11 dans `tests/test_import_fmsave.py`.

## Comments

23/11/2026 — expert : APPROVED (empreinte 6720e3fc). QC : VALIDÉ. Clôture journalisée : VALIDÉ.
- Remarques facultatives : chiffres du journal alignés sur la dernière exécution (A1, fait) ; cellule d'attribut vide dans la sauvegarde = valeur du classeur gardée (A2, improbable, non traité) ; lecture du statut gardien asymétrique, sans effet observé (A3).
- Pour 06b : `compute_moyenne_fm.py` puis `generate_national_teams.py` juste après `--write` ; mesure avant/après (V1 et V2) ; vérifier que la mise en forme du classeur est conservée.
- Durée : estimée 110 min, réelle environ 150 min (+ 36 %) : analyse 35, développement 50, tests 35, vérifications 30. Écart > 30 % : deux défauts découverts par la mesure avant revue (échelle 1-20 / 5-99, contrôle de poste trop strict) et départage des incertitudes ajouté à la demande du propriétaire (club, valeur marchande). Temps machine hors total : deux suites complètes (13 min ; une interrompue).
