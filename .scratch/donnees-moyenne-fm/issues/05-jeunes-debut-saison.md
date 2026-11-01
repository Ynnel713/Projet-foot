# 05: Audit des Moyennes FM — jeunes joueurs qui s'imposent en début de saison 2026-27

**What to build:** Relever légèrement la Moyenne FM des joueurs de 23 ans ou moins devenus titulaires ou décisifs depuis août 2026, avec la méthode par catégorie du ticket 04 (profil progression).

**Status:** livré (01/11/2026), validé expert + QC

**Dépendance :** appliqué par-dessus le lot 1 (ticket 04, commit ec8af48) ; base de revue ec8af48.

**Décisions du propriétaire**
- 01/11/2026 (« analyse les jeunes joueurs qui s'imposent dans leur club en ce début de saison pour que leur note soit revue légèrement si nécessaire ») : demande.
- 01/11/2026 (« Les 15, Yassine à 66 ») : 15 joueurs retenus, Yassine plafonné à 66.
- 01/11/2026 (« Oui, j'accepte ») : réserve A1 de l'expert acceptée, Varela 68 (cible 67), Athekame 68 (67), Raimondo 65 (64,5), Potulski 63,5 (63), valeurs obtenues par saut de rang.
- 01/11/2026 (« Yassine à 68 ») : 66 inatteignable (la note passe de 63,5 à 68 dès le premier attribut relevé, trou dans le classement des ailiers droits) ; 68 retenu.

## Critères d'acceptation

- [x] Sauvegarde intégrale avant écriture (`data/joueurs_backup_20261101_175636_avant_lot2.xlsx`, `cmp` identique)
- [x] Moyenne FM = valeur validée pour les 15 joueurs : Varela 68, Raimondo 65, Athekame 68, Yassine 68, Mohya 57, Romano 51,5, Potulski 63,5, Gadou 62, Tapé 58, Sousa 57,5, Antwi 50, Coulibaly 51,5, Le Guen 49, Ouzenadji 48, Boissé 39,5
- [x] Témoins inchangés : les 8 cibles du ticket 04, les 4 cas test, Rice 87, Openda 77
- [x] Attributs modifiés uniquement pour ces 15 joueurs, sur les seuls attributs de poids > 0 du poste noté ; aucune inversion d'ordre à l'intérieur d'une catégorie ; trois points forts inchangés ; tous les attributs de la base dans [5, 99]
- [x] Aucune autre colonne d'« Infos principales » modifiée ; onglets hors sélections identiques ; `_FM_LEVELS` et le code inchangés
- [x] Effet induit documenté : 81 autres joueurs baissent de 0,5 à 1 point ; aucun changement de composition en sélection
- [x] Suite complète verte : 2 244 passés, 13 désélectionnés, 0 échec (01/11/2026 ; +22 par rapport au ticket 04 venant de tests ajoutés hors de ce ticket dans l'arbre de travail, aucun ne portant sur ces cellules)

Journal détaillé : `.scratch/donnees-moyenne-fm/journal-05-jeunes-debut-saison.md`.

## Comments

**01/11/2026 — sources** : recherche web du 01/11/2026 (Il Post 26/10, FotMob, ligainsider 20/10, footballeur.fr). Seulement 6 à 8 journées : hausses limitées (+3 à +7), à revoir à la trêve. Fiabilité moyenne pour Varela, Raimondo, Athekame, Mohya, Potulski, Gadou ; faible pour les autres.

**01/11/2026 — /valider-ticket-simulafoot** (empreinte 42b601ef…, base ec8af48)
- Expert : APPROVED_WITH_RESERVATIONS. Réserve A1 (4 valeurs au-delà de la cible annoncée) acceptée par le propriétaire (« Oui, j'accepte »). Facultatif : A2 hausses d'attributs fortes pour les cas de fiabilité faible (λ 0,07 à 0,10, jusqu'à +7 sur un attribut, effet direct en V2), à réexaminer à la trêve, plafonnement de λ à proposer avant le prochain lot ; A3 81 baisses par effet de rang, effet cumulé à suivre.
- QC : VALIDÉ. Non bloquant : non-inversion, points forts et témoins attestés par le journal seulement.
- Clôture : VALIDÉ (journal `donnees-moyenne-fm/05/cloture`).

**Limites connues** : cibles au seuil de leur rang (A1 du ticket 03) ; Palmisani (gardien, Frosinone) sans attributs FM, non traitable par la méthode.
