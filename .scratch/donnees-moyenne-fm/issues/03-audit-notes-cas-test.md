# 03: Audit footballistique des Moyennes FM — cas test

**What to build:** Réévaluer la Moyenne FM de joueurs dont la note ne reflète plus le niveau actuel, en modifiant leurs attributs FM sans dénaturer leur profil, puis recalculer la colonne. Ce ticket couvre les 5 cas test exigés avant généralisation (lot prioritaire : ticket ultérieur).

**Status:** livré (31/10/2026), validé expert + QC

**Décisions du propriétaire (31/10/2026)**
- Méthode (« Oui, les quatre ») : agir sur les attributs puis relancer `compute_moyenne_fm.py` (pas de colonne de correction) ; attributs entiers de 5 à 99 (plus seulement des multiples de 5) ; facteur multiplicatif unique sur les attributs de poids > 0 pour le poste noté ; 5 cas test d'abord, puis lot prioritaire de 100-150 joueurs.
- Cibles (« Oui, les cinq ») : Brunner 55 → 72, Karl 75,5 → 79, Lewandowski 83,5 → 78, Modrić 85 → 81, Rice 87 inchangé.

## Critères d'acceptation

- [x] Sauvegarde intégrale avant écriture (`data/joueurs_backup_20261031_183254.xlsx`, `cmp` identique)
- [x] Moyenne FM après recalcul = cible exacte pour les 5 joueurs
- [x] Attributs modifiés uniquement pour les 4 joueurs corrigés ; aucune inversion d'ordre entre leurs attributs ; tous les attributs de la base dans [5, 99]
- [x] Aucune autre colonne d'« Infos principales » modifiée (Moyenne joueur, postes, clubs… identiques) ; `_FM_LEVELS` et le code inchangés
- [x] Effet induit documenté : 56 autres joueurs bougent de 0,5 à 1,5 point (remise à l'échelle par rangs) ; sélections régénérées (2 changements de composition)
- [x] Suite complète verte : 2 125 passés, 13 désélectionnés, 0 échec (31/10/2026 ; +1 par rapport à la référence 2 124, venant de modifications préexistantes non liées de l'arbre de travail)

Journal détaillé (attributs avant/après, justifications, joueurs déplacés) : `.scratch/donnees-moyenne-fm/journal-03-cas-test.md`.

## Comments

**31/10/2026 — sources** : Footmercato, Matchscan, UEFA (Brunner) ; FotMob, Bundesliga.com, Wikipedia (Karl) ; FotMob, FootyStats, The Analyst, Sofascore (Lewandowski) ; FBref, FotMob (Modrić) ; FotMob, BeSoccer (Rice). Saison 2026-27 à ~10 journées : fiabilité moyenne, sauf Rice.

**31/10/2026 — /valider-ticket-simulafoot** (empreinte 8bf0f5b6…, commit 7318838)
- Expert : APPROVED. Facultatif : A1 cibles au seuil de leur rang, à revérifier après le recalcul du lot suivant ; A2 le facteur unique modifie aussi le mental et les coups de pied arrêtés (Détermination de Lewandowski 90 → 83, penalty de Brunner 80 → 86), méthode par catégorie à soumettre au propriétaire avant le lot.
- QC : VALIDÉ. Non bloquant : justifications footballistiques non vérifiables dans le dossier (cibles décidées par le propriétaire).
- Clôture : VALIDÉ (journal `donnees-moyenne-fm/03/cloture`).

**Limites connues** : le facteur unique baisse aussi le mental d'un vétéran (Détermination de Lewandowski 90 → 83), alors qu'un déclin réel est surtout physique ; décalage maximal d'un voisin 1,5 point (Sporar), au-delà des ±0,5 annoncés.
