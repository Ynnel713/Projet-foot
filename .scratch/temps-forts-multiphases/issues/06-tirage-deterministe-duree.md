# 06: Tirage déterministe de la durée (10-40s), décorrélé de l'issue

**What to build:** le nombre de phases de construction (1 à 3) et la durée totale d'un temps fort sont tirés déterministiquement (sha256 de `event_ref`), avec un plancher strict de 10 secondes et un plafond de 40 secondes, sans aucune dépendance au fait que l'événement se conclue par un but ou non. L'utilisateur ne peut plus deviner l'issue à partir de la durée du clip.

**Blocked by:** 05 (généralisation complète aux 12 gabarits).

**Status:** ready-for-agent

- [ ] 0 clip sous 10 secondes et 0 clip au-dessus de 40 secondes sur l'échantillon de référence
- [ ] Sur l'échantillon, aucune corrélation statistique mesurable entre durée et issue (but / non-but)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Propriétaire valide, sur un échantillon de clips mélangés, qu'il ne peut pas deviner l'issue à partir de la durée

**Note :** fichiers sous exception (`CLAUDE.md`) concernés selon ce qui est réellement touché — demander l'exception avant de coder.
