# 08: Jouer à dix : resserrer, protéger l'axe, couvrir avant d'attaquer

**Chantier :** `v2-coach-et-gestion-de-match` (audit de la gestion de match du 26/11/2026, demande du propriétaire, ticket proposé « G2 »). **Catégorie :** décision collective.

**Constat vérifié (26/11/2026) :**
- Il n'y a ni carton ni expulsion dans `v2engine/` aujourd'hui (seule la gravité de la faute existe : `duel.py`, « sans carton, jaune, rouge »).
- `v2-attributs-restants/09a` prévoit l'expulsion et « une équipe à 10 qui se réorganise sans téléportation », sans dire comment elle joue. `05b` traite le remplacement après une expulsion.
- Rien ne change le comportement d'une équipe en infériorité numérique, ni celui de l'adversaire en supériorité :
  - compacité du bloc ;
  - joueurs projetés ;
  - rôles de couverture ;
  - pressing.

**What to build:** dès que l'équipe a un joueur de champ de moins que l'adversaire (expulsion, ou blessure sans remplaçant disponible : `v2-attributs-restants/09b`), la structure de consignes d'équipe (`v2-realisme/13a`) reçoit un décalage « infériorité numérique », par les leviers existants seulement :
1. **Resserrer** : bloc moins large et lignes plus proches (leviers de `v2-realisme/13c` et `10m2`), sans changer la formule du bloc.
2. **Moins attaquer** : moins de joueurs projetés et moins d'appelants (`CALLER_CAP`, `02g`), pressing déclenché moins haut (`13b`).
3. **Protéger l'axe** : la couverture de l'axe passe avant le couloir dans l'attribution des rôles défensifs (`v2-collectif/07`).
4. **Rôles de couverture prioritaires** : quand la formation perd un joueur, les rôles de couverture (`13h` : au moins un par côté) sont pourvus en premier, avant les rôles de projection. Le poste du joueur expulsé est réparti selon la table de `13h`.

Le décalage se combine à la gestion du score (02) : une équipe à dix menée en fin de match se découvre quand même, moins vite. Son amplitude est bornée par le budget tactique de `13j`. **L'adversaire en supériorité** ne reçoit aucune consigne nouvelle : son surnombre agit par le jeu lui-même (un joueur libre de plus, lu par la décision, `v2-realisme/30b`).

**Attributs :** aucun nouveau. Teamwork reste la discipline individuelle (tenir sa place), comme au `13k` : le décalage agit sur des paramètres d'équipe, jamais sur la décision d'un joueur.

**Constantes à proposer avant le code :** ampleur de chaque décalage (largeur, distance entre lignes, joueurs projetés, hauteur de déclenchement du pressing), priorité de l'axe. Chiffres réels à sourcer, sinon « non trouvé » : buts marqués et encaissés par minute après une expulsion, possession à 10 contre 11. Pistes non lues : Vecer, Kopriva et Ichiba (2009), effet du carton rouge ; Titman et al. (2015), cartons et intensités de buts.

**Blocked by:** `v2-attributs-restants/09a` (l'expulsion) ; `09b` pour le cas « blessure sans remplaçant » (dépendance partielle : branché et testé à sa livraison) ; `v2-realisme/13a`, `13j`, `13h` (structure, budget, rôles) ; 02 (combinaison avec le score).

**Bloque :** aucun (passe après `v2-collectif/22c`, comme 09a et 05b : contrôle de non-régression).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : 09a, 13a, 13h, 13j livrés ; chaque décalage passe par un levier existant ; scènes à 10 contre 11 faites par la fabrique `01f`. Découpage examiné : non retenu (les quatre décalages sont une même consigne, testés ensemble ; 5 min au-dessus du seuil).
Temps machine, non compté : suite complète (environ 10 min) ; scénarios forcés (expulsion imposée à la 30e et à la 70e, N graines fixées avant la mesure).

## Tests

- **Scènes :** même équipe à 11 puis à 10, après une expulsion comme après une blessure sans remplaçant (même décalage) : bloc moins large et lignes plus proches, moins de joueurs au-delà du ballon ; formation privée d'un latéral : un rôle de couverture reste pourvu de chaque côté ; à 10 et menée à la 85e : bloc plus haut qu'à 10 à égalité, mais plus bas qu'à 11 menée.
- **Statistiques (scénarios forcés) :** buts pour et contre par minute après l'expulsion, possession, tirs, comparés aux mêmes graines sans expulsion.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] À 10, compacité et joueurs projetés mesurablement différents d'à 11 dans le sens attendu (scènes) ; aucune téléportation au changement (test)
- [ ] Rôles de couverture pourvus avant les rôles de projection quand un joueur manque (test, règle de `13h` vraie après l'expulsion)
- [ ] Combinaison avec le score : effet progressif, jamais une bascule à une minute fixe (02)
- [ ] En scénarios forcés : écart de buts et de possession dû à l'expulsion rapporté et comparé au réel, sans réglage générique
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
