# 06: Tirage déterministe de la durée (20-40s), décorrélé de l'issue

**What to build:** le nombre de phases de construction (1 à 3) et la durée totale d'un temps fort sont tirés déterministiquement (sha256 de `event_ref`), avec un plancher strict de 20 secondes et un plafond de 40 secondes sur la durée AJOUTÉE par la construction, sans aucune dépendance au fait que l'événement se conclue par un but ou non. L'utilisateur ne peut plus deviner l'issue à partir de la durée du clip. **Exception validée par le propriétaire (22/10/2026)** : si la conclusion existante (inchangée) dépasse déjà 40 secondes à elle seule, la construction n'ajoute aucune seconde et la durée totale dépasse 40 secondes en conséquence — la conclusion n'est jamais raccourcie pour tenir ce plafond.

**Blocked by:** 05 (généralisation complète aux 12 gabarits).

**Status:** livré, validé QC (sous-étape `temps-forts-multiphases-06`, 23/10/2026) — reste la validation visuelle du propriétaire

- [ ] 0 clip sous 20 secondes ; 0 clip au-dessus de 40 secondes sur l'échantillon de référence, sauf les clips dont la conclusion seule dépasse déjà 40 secondes (exception validée ci-dessus)
- [ ] Sur l'échantillon, aucune corrélation statistique mesurable entre durée et issue (but / non-but)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Propriétaire valide, sur un échantillon de clips mélangés, qu'il ne peut pas deviner l'issue à partir de la durée

**Note :** fichiers sous exception (`CLAUDE.md`) concernés selon ce qui est réellement touché — demander l'exception avant de coder.

**Exception accordée (23/10/2026) :** le propriétaire a validé l'exception `CLAUDE.md` pour `src/ligue1sim/animation/templates.py` et `engine/narrative_player.py` (aucun autre fichier interdit touché, `ball_events.py` inchangé).

**Mesure avant correction (pipeline réel, 100 matchs, graine d'audit, 1552 clips) :** buts 28,4 s en moyenne contre 31,7 s ; AUC 0,395 (0,5 = aucune information) ; 22 clips sous 20 s, 92 à 40 s ou plus. Deux causes : la suite du tir (rebond, parade) ajoutée par le lecteur après la séquence, absente du calcul de durée ; et la construction omise sur un but sans passeur crédité.

**Décisions du propriétaire (23/10/2026) :**
- La durée FINALE du clip (suite du tir comprise) est tirée par sha256 de `event_ref` à partir de la conclusion la plus longue parmi TOUTES les issues possibles de l'action ; la construction absorbe l'écart. Durée identique, au bit près, quelle que soit l'issue.
- But sans passeur crédité : la construction s'ancre sur la position du ballon au départ, jamais omise.
- « Nombre de phases 1 à 3 » sorti de ce ticket (n'aide pas à cacher l'issue ; variété visuelle, ticket à part non planifié, chantier en pause).
- Résidu accepté et documenté : la conclusion la plus longue possible dépend de la géométrie de l'action, qui diffère légèrement entre buts et occasions (génération en amont du rendu) ; aucun tirage ne peut l'effacer sans réduire fortement la variété ou raccourcir des conclusions.

**Mesure après correction (même échantillon) :** 0 clip sous 20 s, 0 à 40 s ou plus ; AUC globale 0,549 (p = 0,013) ; seul `debordement_centre_tete` reste nettement détectable (AUC 0,674, p = 0,001) ; les 11 autres gabarits sont non significatifs après correction pour tests multiples. Coût de calcul inchangé (10,9 s par match avec ou sans).
