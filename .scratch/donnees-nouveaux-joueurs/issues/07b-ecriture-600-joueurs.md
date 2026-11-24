# 07b: Écriture des 600 joueurs de la sauvegarde FM et fichier des nations

**Status:** livré (24/11/2026), validé expert + QC

**Blocked by:** 07a (livré)

**What to build:** lancer `scripts/add_fmsave_players.py --write` (ajout des 600 joueurs et fichier `data/nouveaux_joueurs_nations.xlsx` : Nom, Prénom, Poste, Club, Nation vide), puis `scripts/compute_moyenne_fm.py` et `scripts/generate_national_teams.py` ; vérifier le classeur et mesurer l'effet. Aucun code modifié.

**Décision du propriétaire (23/11/2026) :** « rajoute les 600 joueurs suivants […] Une fois que c'est fait, génère moi un excel avec ces nouveaux joueurs (juste nom + prénom + poste + club rien d'autre et une colonne nation que je remplirai) ».

**Estimation (travail effectif) :** analyse 10 min, application et recalculs 15 min, tests 15 min, vérifications et mesures 30 min ; total 1 h 10 ; confiance élevée. Temps machine hors total : suite complète, calibration V1 des 9 championnats avant / après.

## Critères d'acceptation
- [x] 600 lignes ajoutées (7 473 -> 8 073), mêmes lignes existantes inchangées hors Moyenne FM ; ID uniques ; `Tableau8` étendu ; rapport identique à l'essai à blanc du 07a.
- [x] Moyenne FM : 0 changement pour les 7 473 joueurs existants ; nouveaux joueurs notés sur la courbe de leur famille ; aucune ligne sans Moyenne FM.
- [x] Fichier des nations : 600 lignes, colonnes exactement Nom, Prénom, Poste, Club, Nation (vide).
- [x] Chargeurs V1 sans erreur (9 championnats, vivier perso) ; aucun effectif au-delà de 40 hors « Sans club » ; sélections régénérées (les « À renseigner » ignorés).
- [x] Mesure V1 avant / après (calibration à graine fixée, 9 championnats).
- [x] Suite complète passée.

## Journal

24/11/2026 — implémenté (données seules, aucun code modifié).
- `add_fmsave_players.py --write` : 600 joueurs ajoutés (ID 7 654 à 8 253) ; rapport identique à l'essai à blanc validé du 07a (hors statut AJOUTÉ / PRÉVU) ; destination 28 dans les 9 championnats, 409 dans un club « Autres clubs » existant, 41 sans club, 122 dans des clubs créés. Copie de secours supprimée (non suivie, version précédente dans git).
- Classeur : 7 473 -> 8 073 lignes ; `Tableau8` A1:BQ7474 -> A1:BQ8074 ; **aucune cellule modifiée dans les 7 473 lignes existantes** (Moyenne FM comprise, comparaison cellule par cellule) ; ID uniques ; 600 « À renseigner ».
- Moyenne FM des nouveaux : sur la courbe de leur famille (ticket 02), 0 vide, de 55,5 à 85 (moyenne 72,1).
- Effectifs : aucun au-delà de 40 hors « Sans club » du fait de l'ajout (São Paulo FC était déjà à 43 avant ; plafond respecté, aucun ajout).
- Chargeurs V1 : 9 championnats, 174 clubs ; vivier perso 214 clubs (inchangé) ; 872 clubs au total.
- Sélections : 129 pays, 91 complets avant comme après ; « À renseigner » ignoré (avec les 6 nationalités déjà ignorées).
- Fichier des nations `data/nouveaux_joueurs_nations.xlsx` : 600 lignes, colonnes Nom, Prénom, Poste, Club, Nation (vide) ; envoyé au propriétaire.
- V1, calibration à graine fixée (30 saisons par championnat) : Premier League, Bundesliga, Jupiler Pro League strictement identiques ; ailleurs, seules les notes des clubs qui reçoivent des joueurs montent (+ 0,2 à + 1,9 : Groningen 58,1 -> 60,0, Coruña 72,0 -> 73,7, AZ 70,6 -> 72,0, Go Ahead Eagles 59,0 -> 60,5, Venezia 68,5 -> 69,8, Brest 71,1 -> 72,3) ; buts par match à ± 0,02 partout.
- Suite complète : 3 557 passés, 14 désélectionnés (17 min 14), aucun test adapté.

## Comments

24/11/2026 — expert : APPROVED (empreinte 90acb559). QC : VALIDÉ. Clôture journalisée : VALIDÉ.
- Remarques facultatives : notes des nouveaux bornées au sommet de la courbe de leur famille (85 au plus : un très fort joueur FM comme Messi peut être sous-noté ; négligeable, club créé hors des 9 championnats) ; compte attendu de `CLAUDE.md` (3 452) périmé (3 557), ticket documentaire à prévoir avec l'accord du propriétaire.
- Suite : au retour du fichier des nations rempli, reporter les nationalités et régénérer les sélections ; 14 À_VÉRIFIER écartés (6 probablement nouveaux) ; 122 joueurs en clubs créés jouables seulement si leur club devient complet.
- Durée : estimée 70 min, réelle environ 55 min (− 21 %) : analyse 10, application et recalculs 10, tests 10, vérifications et mesures 25. Temps machine hors total : 18 calibrations V1 de 30 saisons, suite complète (17 min).
