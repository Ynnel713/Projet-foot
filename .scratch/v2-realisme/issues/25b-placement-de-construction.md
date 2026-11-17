# 25b: Placement de construction quand le gardien ou un central a le ballon

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : jeu sans ballon et placement dynamique comme cœur du jeu ; audit de la roadmap du même jour). **Priorité :** P1 (la sortie de balle n'existe pas : `v2-collectif/15` et `v2-attributs-restants/03c` choisiraient entre des solutions que personne ne crée). **Catégorie :** placement.

**Constat vérifié (14/11/2026) :** la place avec ballon est un décalage fixe par rôle (`bloc.ROLE_PLACE_WITH_BALL` : défenseur central (0, 0), sentinelle −4 m), identique que le ballon soit chez le gardien ou dans le dernier tiers. Sur une sortie de but, `restart.place` n'éloigne que les adversaires. Les centraux et les milieux défensifs ne sont jamais appelants (`cerveau.CALLER_ROLES`, `_call_rank` : seuls les joueurs devant le ballon).

**What to build:** une phase « construction » (ballon au gardien ou à un défenseur dans son propre tiers, sortie de but comprise) avec sa propre table de décalages par rôle : centraux qui s'écartent vers les angles de la surface, sentinelle ou regista qui décroche dans l'axe entre eux ou devant eux, latéraux qui montent et s'ouvrent, milieux relayeurs qui se placent dans les demi-espaces. La table s'ajoute à `ROLE_PLACE_WITH_BALL` comme la table sans ballon du 02e ; la place reste ensuite corrigée par l'espace libre (25a) et par Teamwork. Sous pressing haut adverse, les mêmes joueurs restent plus proches du porteur (distance validée) ; sans pressing, ils s'écartent au maximum.

**Hors de ce ticket :** choix du porteur entre court et long (`v2-collectif/15`) ; qualité de la relance du gardien (`v2-attributs-restants/03c`).

**Attributs :** aucun (structure collective ; Teamwork garde son rayon de tolérance).

**Blocked by:** 02d (livré), 02e (livré), 09j (hauteur de la dernière ligne avec ballon, ajouté le 16/11/2026 : la construction ajuste cette hauteur). Indépendant du 25a.

**Bloque :** `v2-collectif/15`, `v2-attributs-restants/03c`, 25d, 25h.

**Status:** livré (17/11/2026), validé expert + QC

**Constantes validées par le propriétaire le 17/11/2026 (« Je valide ») :**
- Phase « construction » : ballon au gardien, ou à un défenseur (DC, LB, RB, LWB, RWB) à moins de 35 m de son but (`BUILD_UP_ZONE_M`), ou sortie de but pour l'équipe ; pendant une passe partie de l'un d'eux, la phase continue jusqu'au contrôle suivant.
- `ROLE_PLACE_BUILD_UP` (avance, écart vers la touche, en mètres, ajoutés à la place avec ballon) : défenseur central (0, +8) ; sentinelle (−6, 0) ; regista (−8, 0) ; récupérateur (−3, 0) ; latéral (+6, +10) ; latéral défensif (+3, +8) ; piston (0, +6) ; milieu relayeur, mezzala, box to box (0, +4) ; autres rôles (0, 0). Personne à moins de 2 m de la touche (`BUILD_UP_TOUCHLINE_M`).
- Pressing haut : adversaires de champ dans nos 35 m ; 2 ou moins, écartement complet ; 4 ou plus, moitié (`BUILD_UP_PRESS_COUNT`, `BUILD_UP_PRESS_SPREAD`) ; linéaire entre. Seul l'écart vers la touche est réduit.
- Hauteur de ligne du 09j inchangée (plancher 15 m, au niveau de la surface).
- Cibles : sortie de but sans pressing, centraux écartés d'au moins 32 m et sentinelle à 18 m au plus du gardien ; sous pressing, centraux plus proches d'au moins 6 m.
- Solutions du gardien porteur : la cible « au moins 4,5 » (tirée de deux mi-temps, 4,6) est remplacée le 17/11/2026 par décision du propriétaire (« Au moins 2 et pas de baisse ») : **au moins 2 en moyenne et pas de baisse par rapport à avant**, la valeur de départ sur 50 matchs étant 3,25.
- Chiffres réels : non trouvés dans une source (ordres de grandeur tactiques).

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : détection de la phase sur la situation existante (`situation.py`) plus la position du ballon ; décalages tactiques sans chiffre réel (ordres de grandeur, « non trouvé » probable).
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Scènes :** sortie de but sans pressing : écart entre les deux centraux au moins égal à la valeur validée, sentinelle à moins de la distance validée du gardien ; même scène sous pressing haut : centraux plus proches.
- **Statistiques (50 matchs) :** part des relances courtes du gardien, pertes dans son propre tiers, solutions de passe du gardien.

## Acceptance criteria

- [x] Constantes produit (décalages par rôle, seuil de pressing) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [x] Gardien porteur : au moins deux solutions de passe ouvertes en moyenne et pas de baisse (critère du propriétaire du 17/11/2026) : 3,57 contre 3,25 avant
- [x] Décalages visibles dans la trace (phase et place de référence)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (aucun attribut lu : test inchangé, vert)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Réalisation (17/11/2026)

- `v2engine/bloc.py` : constantes ci-dessus ; `Bloc.update` détermine la phase de chaque équipe (`_update_build_up`, champ `build_up` : équipe -> part de l'écartement gardée) et `Bloc.in_build_up(team)` ; `Bloc.reference`, avec ballon et en construction, décale la place finale (après mise à l'échelle et écarts entre lignes du 09e) par `_build_up_place` : avance vers le but adverse, écart vers la touche réduit sous pressing, borné à 2 m de la touche, rien pour un joueur dans l'axe. Teamwork garde son rayon de tolérance (`replacement` inchangé).
- `v2engine/cerveau.py` : la raison des intentions « tenir sa place » / « se replacer » (avec ou loin du ballon) et du replacement sur ballon mort (hors engagement) se termine par « (construction) » pendant la phase (`_build_up_note`) ; la cible tracée est la place de référence.
- Tests : 6 ajoutés (`tests/test_v2engine_bloc.py`) : rôles de la table connus ; sortie de but sans pressing (centraux écartés de 33,6 m, + 16 m ; sentinelle à 18 m au plus du gardien, 6 m plus bas ; latéraux + 6 m et ouverts sans franchir 2 m ; relayeurs + 4 m de l'axe ; autres rôles inchangés) ; pressing (4 adversaires : écartement 0,5, centraux 8 m plus proches ; 3 : 0,75) ; début et fin de la phase (passe en vol, contrôle d'un milieu, défenseur au-delà de 35 m) ; sans ballon inchangé et équipe extérieure en miroir ; « (construction) » dans la raison tracée.

**Mesures :** séries de 50 matchs aux graines du banc (`AUDIT_SEED + k`, k = 0 à 49, mêmes affiches que `scripts.measure_v2`), avant (`d82179e`) et après, script hors dépôt `serie_25b.py` (relevés 2 fois par seconde de jeu) :

| Indicateur | Avant | Après |
|---|---|---|
| Solutions ouvertes du gardien porteur (moyenne ; part ≥ 2) | 3,25 ; 80 % | 3,57 ; 85 % |
| Sortie de but : écart des centraux (toutes scènes, pressing compris) | 16,9 m | 27,1 m |
| Sortie de but : sentinelle (ou regista, récupérateur) la plus proche du gardien | 19,3 m | 15,0 m |
| Relances du gardien en jeu par match ; part courte (< 25 m) | 15,5 ; 98,2 % | 15,9 ; 97,7 % |
| Relances gardées (premier contrôle par l'équipe) | 92,6 % | 92,1 % |
| Pertes de balle par match ; dans son propre tiers (35 m) | 259,9 ; 14,8 | 254,7 ; 14,6 |
| Buts par match | 5,40 | 4,98 (− 8 %) |
| Tirs par match | 41,9 | 40,5 (− 3 %) |

Mesure de départ, deux mi-temps (graines 20260923 et 20260924), sortie de but : centraux écartés de 18,5 m, sentinelle à 22 m du ballon, latéraux à 25 m de hauteur et à 14,6 m de la touche, relayeurs à 10,7 m de l'axe. Aucun écart de plus de 10 % sur les volumes (buts − 8 %).

Suite complète : 3 191 passés, 0 ignoré, 14 désélectionnés (3 185 + 6) ; `CLAUDE.md` mis à jour.

Déterminisme : deux exécutions à graine fixée (20260923, 30 min de jeu) : mêmes empreintes (événements `af6bd54f51adef27`, ticks `e80ea2cf261f2c01`).

**Durée :** estimée 1 h 45 ; réelle environ 1 h 25 de travail effectif (analyse 25, développement 20, tests 20, intégration et vérifications 20), à l'horloge de la session, non chronométrée ; écart − 19 %. Temps machine hors total : deux mesures de deux mi-temps, une suite complète (12 min 43), deux séries de 50 matchs (la série « avant » bloquée dans son pool de processus et relancée, environ 40 min), deux empreintes.

## Comments

- **17/11/2026, passage 1** — Expert : `APPROVED`. QC : `VALIDÉ`. Clôture journalisée : `VALIDÉ` (expert APPROVED, QC VALIDÉ). Aucune anomalie bloquante. Améliorations facultatives de l'expert, non bloquantes :
  - A1 : un joueur qui tient sa place (dans sa tolérance Teamwork) trace sa position actuelle et la mention « (construction) », pas la place de référence de construction ; seuls ceux qui se replacent tracent cette place.
  - A2 : sur un ballon libre après un contre ou un tacle, la phase reste à l'équipe qui construisait jusqu'au contrôle suivant.
  - À surveiller : l'écart réel des centraux sur sortie de but sans pressing seul (25d ou `v2-collectif/15`) ; la tendance des buts (− 8 %, non significatif sur 50 matchs).

