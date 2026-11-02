# 06: Enrichissement des données (gestes préférés, pied fort)

**What to build:** Rendre les tickets 04 et 05 visibles sur la majorité des joueurs. Aujourd'hui `Preferred moves` est renseigné pour 40,3 % des 7 473 lignes de `data/joueurs.xlsx` et `Pieds` pour 39,1 % (mesuré le 02/11/2026). Compléter ces colonnes depuis la même source que les attributs (FMInside, `scripts/scrape_fminside_attributes.py`, colonne `FMInside URL`), en priorisant les joueurs des compétitions jouées.

**Attributs :** Preferred moves, Pieds.

**Blocked by:** —

**Status:** à faire (le scraping connecté est une action du propriétaire ; Claude prépare la liste priorisée et vérifie le résultat)

**Point de vigilance :** une ligne laissée vide reste neutre ; ne jamais inventer un geste ou un pied fort. `(aucun)` est une valeur explicite, distincte de vide.

- [ ] Taux de remplissage avant/après, par compétition, publié dans le journal du ticket
- [ ] Aucun geste hors des valeurs connues (ou nouvelle valeur signalée au ticket 05)
- [ ] Suite complète passée
