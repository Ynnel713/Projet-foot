# 23: Hors-jeu

**What to build:** La règle du hors-jeu (Lois du jeu, loi 11) dans le moteur V2. Au départ d'une passe vers l'avant, un attaquant plus proche de la ligne de but adverse que le ballon et que l'avant-dernier adversaire, dans la moitié adverse, est en position de hors-jeu ; s'il reçoit le ballon, coup franc indirect pour l'adversaire. Les joueurs en tiennent compte : les attaquants règlent leurs appels sur la ligne adverse (rester en jeu, partir au moment de la passe), la ligne défensive peut monter pour mettre hors-jeu, avec le risque d'être prise dans le dos.

**Attributs :** Off the Ball (timing de l'appel, rester en jeu) ; Positioning et Teamwork (tenir la ligne ensemble) ; Anticipation (sentir le moment de la passe). Concentration plus tard (oubli d'un défenseur qui couvre l'attaquant).

**Blocked by:** 05 (hauteur de ligne).

**Status:** livré (28/10/2026)

**Pourquoi (27/10/2026) :** sans hors-jeu, une ligne haute laisse dans son dos un espace que rien n'interdit d'exploiter ; le ticket 05 doit donc garder la ligne derrière l'attaquant adverse le plus avancé, et un attaquant qui reste haut fait reculer toute la ligne. Ajouté à la demande du propriétaire.

- [x] Position de hors-jeu jugée au départ de la passe (ballon, avant-dernier adversaire, moitié adverse), coup franc indirect si l'attaquant hors-jeu reçoit : `v2engine/offside.py`, jugement dans `match._step_ball`, coup franc au défenseur de champ le plus proche (jamais le gardien), fautif écarté 1,5 s
- [x] Hors-jeu par match dans une fourchette réelle : réel 3,2-3,5 par match, soit 1,6-1,8 par équipe (Ligue 1 2023-24 et 2024-25, Premier League 2024-25 : 3,54). Mesuré sur 20 matchs : **3,5 par match, 1,75 par équipe**
- [x] Les appels partent au moment de la passe plutôt qu'en restant hors-jeu : Off the Ball règle la ligne (99 → 95 %, 55 → 75 %, 11 → 55 %) ; la ligne défensive ne recule plus systématiquement avec l'attaquant le plus avancé (garde-fou du ticket 05 remplacé par le piège de 5 m)
- [x] Trace et écran V2 : `OffsideEvent` (`trace.py`), `offsides` dans l'API, bandeau « ⚑ Hors-jeu — joueur (équipe) » sur l'écran de match, journal de décision « hors-jeu sifflé, il recule vers sa place »
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18) : Off the Ball (respect de la ligne) et Anticipation (voir le drapeau) ont chacun un effet propre, `line_lag_s` ne lit que Teamwork (le Positioning agit déjà par l'erreur de placement du ticket 04)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code : tolérance 0,3 m, profondeur de piège 5 m, courbe Off the Ball 95/75/55 %
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée : 143 tests V2 verts, 173 avec l'API

**Reporté du ticket 05 (27/10/2026, décision du propriétaire) :** avec la ligne défensive à sa hauteur réelle, tirs et buts sortent des fourchettes (20 matchs : 18,1 tirs par équipe, 4,7 buts par match ; réel 8-15 et 2-3,5). Les tirs de contre-attaque après une récupération dans son camp doublent (4,8 → 9,5 par match) : les blocs se croisent plus haut et plus serrés, et personne ne se replace encore à la perte. Critère ajouté : mesurer l'effet du hors-jeu sur tirs et buts, et revoir le garde-fou « derrière l'attaquant le plus avancé » du ticket 05.

**Directives comportementales du propriétaire (28/10/2026), toutes implémentées :** le piège est collectif (la ligne monte en bloc, chaque défenseur la suit avec un retard d'autant plus grand que son Teamwork est faible, 0 à 1,5 s) ; « play the whistle » (l'attaquant hors-jeu continue son action, les défenseurs qui voient le drapeau lèvent la main et relâchent leur effort 1,5 s, sans s'arrêter) ; pas de hors-jeu passif pour gêne du gardien, mais toucher le ballon est sifflé ; coup franc au défenseur de champ le plus proche, fautif écarté 1,5 s.

**Mesure sur 20 matchs (ticket 05 → ticket 23, graines 20260923 à 20260942).** Tirs 18,1 → **14,4 par équipe** (fourchette réelle 8-15) ; buts 4,7 → **3,25 par match** (2-3,5) ; tirs de contre après récupération dans son camp 9,5 → **6,1**, dans le camp adverse 20,0 → 15,1 ; hors-jeu **3,5 par match, 1,75 par équipe** (réel 3,2-3,5 et 1,6-1,8) ; hauteur de ligne sans ballon 32,7 → 33,5 m ; écart ligne-ballon 18,8 → 17,9 m ; longueur sans ballon 30,1 → 30,2 m ; compacité autour du ballon 7,5 → 7,4 m ; passes par minute 16,8 → 17,3 ; passes chez l'adversaire 33,8 → 34,0 % ; passes en profondeur 4,1 → 0,9 % (l'attaquant est tenu derrière la ligne, valeur réelle non trouvée) ; tacles 58 → 64,9 ; km par joueur 30,6 → 30,5. La crainte d'une explosion des tirs de contre derrière un piège à +5 m n'est pas vérifiée : le hors-jeu les fait *baisser*.

**Ce qui a été corrigé en route (mesuré, pas supposé).** Première version : 21,5 hors-jeu par match et 28 tirs de contre, parce que le porteur choisissait le coéquipier le plus avancé et le plus libre -- souvent un joueur 5 m au-delà de la ligne -- et que chaque coup franc rendait le ballon à l'adversaire en pleine attaque. Le porteur écarte maintenant les coéquipiers qu'il voit nettement hors-jeu (`PASS_OFFSIDE_MARGIN_M`, 0,5 m, l'angle mort d'un professionnel) : 21,5 → 3,5 hors-jeu par match. Un seuil de 1 m laissait encore 7,5 hors-jeu par match : c'est le seul paramètre qui pilote la fréquence, et c'est une information du joueur, pas un attribut du modèle.

**Non modélisé, assumé :** pas de hors-jeu sur touche, sortie de but ni corner (ces phases n'existent pas encore) ; pas de hors-jeu sur une passe d'un adversaire (aucune déviation modélisée) ; pas de hors-jeu pour gêne du gardien sans toucher le ballon : s'il touche, c'est sifflé, point barre.
