# 10: Retraites internationales supplémentaires

**Status:** livré (24/11/2026), validé expert + QC

**Blocked by:** 08 (mécanisme), 09 (nationalités des nouveaux)

**What to build:** ajouter à `data/retraites_internationales.csv` les joueurs de la liste du propriétaire, puis relancer `scripts/set_international_retirement.py` et `scripts/generate_national_teams.py`. Aucun code modifié.

**Demande du propriétaire (24/11/2026) :** liste de joueurs ayant pris leur retraite internationale (deux captures d'écran) : Neymar, Manuel Neuer, Riyad Mahrez, Guillermo Ochoa, Nicolás Otamendi, Edin Džeko, James Rodríguez, Antonio Rüdiger, Patrik Schick, Enner Valencia, Marko Arnautović, Craig Gordon, Jean Michaël Seri, Marcos Llorente ; « autres joueurs à ajouter » : Édouard Mendy, Iñaki Williams, Seko Fofana ; « Rajoutes y casemiro ».

**Estimation (travail effectif) :** analyse 5 min, application 5 min, vérifications 20 min ; total 30 min ; confiance élevée. Temps machine hors total : suite complète.

## Correspondance avec la base (recherche par nom normalisé, un seul candidat chacun, nationalité cohérente)
- Déjà marqués (ticket 08) : Neymar (2521), Edin Džeko (1086).
- Ajoutés : Manuel Neuer 769, Riyad Mahrez 6605, Guillermo Ochoa 8063, Nicolás Otamendi 3903, James Rodríguez 6393, Antonio Rüdiger 421, Patrik Schick 830, Enner Valencia 3924, Marko Arnautović 7953, Craig Gordon 6478, Marcos Llorente 462, Edouard Mendy 2573, Iñaki Williams 552, Seko Fofana 3552, Casemiro 7660.
- Absent de la base et de la sauvegarde FM : Jean Michaël Seri (rien à marquer, sans effet).

## Critères d'acceptation
- [x] 24 « oui » (9 + 15) ; seule la colonne « Retraite internationale » change dans « Infos principales » (15 cellules).
- [x] Sélections régénérées : aucun des 24 sélectionné ; bilan des remplacements publié.
- [x] Suite complète passée.

## Journal

24/11/2026 — implémenté (données seules).
- `data/retraites_internationales.csv` : 15 lignes ajoutées (24 joueurs). `set_international_retirement.py` : 24 « oui », 15 cellules modifiées ; comparaison avant / après : seule la colonne « Retraite internationale » change.
- Sélections régénérées : 129 pays, 91 complets (inchangé) ; aucun des 24 sélectionné. Remplacements : Argentine Otamendi -> Nahuel Molina ; Autriche Arnautović -> Elias Havel ; Brésil Casemiro -> Lucas Paquetá ; Côte d'Ivoire Seko Fofana -> Malick Yalcouyé ; Colombie James Rodríguez -> Miguel Monsalve ; République tchèque Schick -> Mojmír Chytil ; Algérie Mahrez -> Anis Hadj Moussa ; Équateur Enner Valencia -> Kevin Rodríguez ; Mexique Ochoa -> Raúl Rangel ; Sénégal Édouard Mendy -> Demba Thiam. Neuer, Rüdiger, Llorente, Craig Gordon et Iñaki Williams n'étaient pas retenus (note).
- Suite complète : 3566 passés, 14 désélectionnés.

Correspondances ID -> nom du classeur (sortie complète de `set_international_retirement.py --dry-run`, revue expert A1) :
- ID 462 : Marcos Llorente (liste : Marcos Llorente)
- ID 2676 : Sadio Mané (liste : Sadio Mané)
- ID 421 : Antonio Rüdiger (liste : Antonio Rüdiger)
- ID 769 : Manuel Neuer (liste : Manuel Neuer)
- ID 3813 : Romelu Lukaku (liste : Romelu Lukaku)
- ID 2521 : Neymar (liste : Neymar)
- ID 2573 : Edouard Mendy (liste : Edouard Mendy)
- ID 830 : Patrik Schick (liste : Patrik Schick)
- ID 552 : Iñaki Williams (liste : Iñaki Williams)
- ID 3552 : Seko Fofana (liste : Seko Fofana)
- ID 6393 : James Rodríguez (liste : James Rodríguez)
- ID 2679 : Cristiano Ronaldo (liste : Cristiano Ronaldo)
- ID 2610 : Karim Benzema (liste : Karim Benzema)
- ID 1522 : Olivier Giroud (liste : Olivier Giroud)
- ID 3924 : Enner Valencia (liste : Enner Valencia)
- ID 6605 : Riyad Mahrez (liste : Riyad Mahrez)
- ID 1086 : Edin Dzeko (liste : Edin Dzeko)
- ID 3903 : Nicolás Otamendi (liste : Nicolás Otamendi)
- ID 6478 : Craig Gordon (liste : Craig Gordon)
- ID 7654 : Lionel Messi (liste : Lionel Messi)
- ID 7655 : Antoine Griezmann (liste : Antoine Griezmann)
- ID 7660 : Casemiro (liste : Casemiro)
- ID 7953 : Marko Arnautović (liste : Marko Arnautović)
- ID 8063 : Guillermo Ochoa (liste : Guillermo Ochoa)

## Comments

24/11/2026 — expert : APPROVED (empreinte e2466175). QC : VALIDÉ. Clôture journalisée : VALIDÉ.
- Remarques facultatives : sortie complète des correspondances ID -> nom archivée ci-dessus (fait) ; compte attendu de `CLAUDE.md` périmé (3 566).
- Durée : estimée 30 min, réelle environ 30 min (0 %) : analyse 10, application 5, vérifications 15. Temps machine hors total : suite complète (15 min).
