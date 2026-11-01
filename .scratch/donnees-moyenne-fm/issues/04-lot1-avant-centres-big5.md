# 04: Audit des Moyennes FM — lot 1, avant-centres des 5 grands championnats

**What to build:** Réévaluer les avant-centres (famille BU) du périmètre Big-5 dont la Moyenne FM ne reflète plus le niveau actuel, avec la méthode par catégorie (profils neutre / déclin / progression), et réappliquer les 4 cas test du ticket 03 avec cette méthode depuis leurs attributs d'origine.

**Status:** livré (01/11/2026), validé expert + QC

**Décisions du propriétaire**
- 31/10/2026 (« Facteurs par catégorie », puis « Oui, tout ») : facteurs par catégorie (déclin : technique 0,4, mental 0,15, physique 1, CPA 0,4, gardien 0,6 ; progression : 1 / 0,8 / 0,5 / 0,5 / 1 ; neutre : 1 partout) ; règle de profil (déclin si baisse et âge ≥ 30, progression si hausse et âge ≤ 23) ; réapplication des 4 cas test ; périmètre Big-5 de 174 joueurs, par lots de famille.
- 31/10/2026 (« cela me semble sévère pour openda, le reste est cohérent ») : Openda maintenu à 77 ; les 8 autres corrections retenues.
- 01/11/2026 (« Oui, applique ») : application du lot.

## Critères d'acceptation

- [x] Sauvegarde intégrale avant écriture (`data/joueurs_backup_20261101_014409.xlsx`, `cmp` identique)
- [x] Moyenne FM = cible exacte pour Malen 82, Marmoush 80, Castro 78, Giroud 76, Aspas 76, Richarlison 76, Dovbyk 74, Boniface 72 ; cas test inchangés (Lewandowski 78, Karl 79, Brunner 72, Modrić 81) ; Rice 87 ; Openda 77
- [x] Attributs modifiés uniquement pour ces 12 joueurs, sur les seuls attributs de poids > 0 du poste noté ; aucune inversion d'ordre à l'intérieur d'une catégorie ; tous les attributs de la base dans [5, 99]
- [x] Aucune autre colonne d'« Infos principales » modifiée ; onglets hors sélections identiques ; `_FM_LEVELS` et le code inchangés
- [x] Effet induit documenté : 21 autres joueurs bougent de 0,5 à 1 point ; 5 changements de composition en sélection
- [x] Suite complète verte : 2 222 passés, 13 désélectionnés, 0 échec (01/11/2026 ; écart avec la référence 2 124 venant de tests ajoutés hors de ce ticket, aucun ne portant sur ces cellules)

Journal détaillé : `.scratch/donnees-moyenne-fm/journal-04-lot1-avant-centres.md`.

## Comments

**01/11/2026 — sources** : recherche web du 31/10/2026 (FotMob, FBref, Transfermarkt, Sofascore, Maxifoot, sites des ligues). Fiabilité élevée pour Malen, faible pour Dovbyk, moyenne pour les autres.

**01/11/2026 — /valider-ticket-simulafoot** (empreinte 56a1d04f…, base 962913a)
- Expert : APPROVED. Facultatif : A1 effet de rang hors famille BU (la baisse de Marmoush, noté AG, remonte d'environ 1 point Doué, Barcola, Rashford, Semenyo, Trincão), à réexaminer au lot Ailiers ; A2 colonne Âge ancienne (Giroud 40, Modrić 41 au 01/11/2026), sans effet sur le profil ; A3 cibles au seuil de leur rang, à revérifier après chaque lot.
- QC : VALIDÉ. Non bloquant : écart du compte de tests non vérifiable dans le dossier ; binaire lu via le diff cellule par cellule.
- Clôture : VALIDÉ (journal `donnees-moyenne-fm/04/cloture`).

**Limites connues** : les cibles restent au seuil de leur rang (A1 du ticket 03), à revérifier après chaque lot ; la colonne Club n'est pas à jour pour plusieurs joueurs (Watkins, Openda, Dovbyk, Castro, Marmoush), hors périmètre.
