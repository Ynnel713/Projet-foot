# 10: Révision du plan à la mi-temps selon la première période

**Chantier :** `v2-coach-et-gestion-de-match` (audit de la gestion de match du 26/11/2026, demande du propriétaire, ticket proposé « G4 »). **Catégorie :** décision du coach.

**Constat vérifié (26/11/2026) :**
- La mi-temps existe dans le moteur (ticket 07, livré) : arrêt, replacement, coup d'envoi ; récupération à la pause au `v2-realisme/20c`.
- Les remplacements de la pause arrivent avec 05a.
- Aucun ticket ne fait réviser au coach ses consignes à la pause selon ce qui s'est passé. La gestion du score (02) dose selon le score et la minute, pas selon le contenu de la première période. Les styles (`v2-realisme/13a` à `13k`) sont fixes pour le match.

**What to build:** à la mi-temps, le coach compare la première période à son plan et décale ses consignes d'équipe (`13a`) pour la seconde, par les leviers existants seulement :
1. **Lecture** : possession, xG pour et contre (`v2-realisme/06c`, xG neutre de la trace), pressing subi (pertes dans son tiers sous pression, banc existant), tirs concédés, sur la première période seulement.
2. **Révision** : une règle courte, proposée au propriétaire. Exemples :
   - pressé et dominé (pertes dans son tiers, xG contre élevé) : jeu plus direct et bloc un cran plus bas ;
   - dominant mais stérile (possession haute, xG faible) : plus de joueurs projetés et plus de largeur ;
   - plan qui marche : rien ne change.
   Le style du coach reste l'intention de départ ; la révision est un décalage autour.
3. **Borne** : amplitude de la révision limitée par le budget tactique de `13j`, et sa justesse réglée par la note du coach (`13k`). Un coach bien noté lit mieux la première période : son décalage va plus souvent dans le bon sens. Un coach moyen corrige moins juste, jamais à contresens systématique. Sans coach : aucune révision.
4. **Trace** : consignes avant et après la pause, raison de la révision.

**Attributs :** aucun. La note du coach agit sur des paramètres d'équipe (`13k`), jamais sur la décision d'un joueur.

**Constantes à proposer avant le code :** seuils de lecture (ce qui compte comme « pressé », « dominé », « stérile »), ampleur des décalages, effet de la note sur la justesse. Chiffre réel à sourcer, sinon « non trouvé » : écart de jeu entre les deux périodes selon le score à la pause (possession, tirs).

**Lien avec l'existant :** ne duplique pas la gestion du score (02), qui continue d'agir en seconde période sur les consignes révisées. Ne duplique pas les remplacements de la pause (05a à 05c), qui choisissent des joueurs, pas des consignes.

**Blocked by:** 07, `v2-realisme/06c` (livrés) ; 02 ; `v2-realisme/13a`, `13j`, `13k`.

**Bloque :** aucun.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (lecture, règle, trace) | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : consignes de `13a` modifiables entre deux périodes ; indicateurs de première période calculables depuis la trace ; budget de `13j` réutilisé comme borne.
Temps machine, non compté : suite complète (environ 10 min) ; scénarios forcés (premières périodes imposées, N graines fixées avant la mesure).

## Tests

- **Scènes :** première période « pressé et dominé » : consignes révisées dans le sens attendu, bornées par le budget ; plan qui marche : aucune révision ; sans coach : aucune révision ; coach bien noté contre coach moyen : révision dans le bon sens plus souvent.
- **Statistiques (scénarios forcés) :** écart entre les deux périodes (possession, xG, pertes dans son tiers) avec et sans révision, aux mêmes graines.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Révision tracée (consignes avant et après, raison) ; amplitude jamais au-delà du budget de `13j` (test)
- [ ] Effet de la note du coach mesurable et borné, neutre sans coach (principe d'amplitude du 26/11/2026)
- [ ] En scénarios forcés : effet de la révision rapporté, sans réglage générique
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
