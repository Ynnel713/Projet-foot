# 05: Catalogue des 58 gestes préférés

**What to build:** v2-collectif/19 intègre les Preferred moves comme penchants dans la **décision du porteur**. Beaucoup de gestes portent sur d'autres moments du jeu (appels, tirs, centres, coups de pied arrêtés, tacles) et dépendent de mécanismes absents aujourd'hui. Ce ticket garantit qu'aucun des 58 gestes présents dans la base ne reste sans effet : chacun est rattaché à un mécanisme et un ticket, puis branché comme un **biais de probabilité** (jamais un ordre) quand ce mécanisme existe.

| Mécanisme | Gestes | Ticket porteur |
|---|---|---|
| Conduite et dribble | Runs With Ball Often / Rarely / Down Left / Down Right / Through The Centre, Likes To Beat Opponent Repeatedly, Knocks Ball Past Opponent, Tries Tricks, Bring Ball Out of Defence, Dwells On Ball, Tries To Play Way Out Of Trouble (aussi v2-collectif/15), Cuts Inside From Left Wing / Right Wing / Both Wings | v2-collectif/19 ; 07 |
| Passe | Plays Short Simple Passes, Plays No Through Balls, Tries Killer Balls Often, Tries Long Range Passes, Likes To Switch Ball To Wide Areas, Plays One-Twos, Dictates Tempo, Stops Play (tempo ; aussi gestion du temps, v2-coach-et-gestion-de-match/02), Looks For Pass Rather Than Attempting To Score, Uses Outside Of Foot (réduit aussi l'usage du pied faible, ticket 04), Likes Ball Played Into Feet (côté passeur : servir dans les pieds) | v2-collectif/19, 13, 14 |
| Appels sans ballon | Gets Forward Whenever Possible, Gets Into Opposition Area, Arrives Late In Opposition Area, Moves Into Channels (couloir entre défenseur central et latéral, pas « entre les lignes »), Comes Deep To Get Ball, Likes Ball Played Into Feet (côté receveur), Plays With Back To Goal, Likes To Try To Break Offside Trap, Stays Back At All Times, Penalty Box Player, Hugs Line (largeur sans ballon ; aussi conduite le long de la ligne) | v2-collectif/16, 23 ; 19 pour la conduite |
| Tir | Shoots From Distance, Refrains From Taking Long Shots, Places Shots, Shoots With Power, Tries First Time Shots, Likes To Round Keeper, Likes To Lob Keeper, Curls Ball | `v2-collectif/28a` (Long Shots, tir) ; 10a et 10b (finitions) |
| Jeu aérien et centres | Crosses Early, Attempts Overhead Kicks, Curls Ball (centres enroulés) | 01 (centre et duel aérien) ; 11 (types de centres) |
| Pied | Avoids Using Weaker Foot, Moves Ball To Left Foot / Right Foot Before Dribble Attempt | 04 |
| Coups de pied arrêtés | Hits Free Kicks With Power, Tries Long Range Free Kicks, Demands to Take Penalties, Possesses Long Flat Throw, Curls Ball (coups francs enroulés) | 02 |
| Gardien | Uses Long Throw To Start Counter Attacks (relance longue **à la main** du gardien, pas une touche ; la traduction NLG « longue touche » est fausse) | 03 |
| Tacle | Dives Into Tackles, Does Not Dive Into Tackles | `09a` (branchement et mesure : tacle glissé du 07a, fautes ; ces deux gestes ne sont pas mesurés une seconde fois ici) |
| Discipline et ambiance | Argues With Officials, Winds Up Opponents (cartons, 09) ; Gets Crowd Going (décision du 03/11/2026 : fréquence et ampleur des célébrations, sans effet sur le jeu) | 09 ; `v2-mise-en-scene/04` |
| Aucun | `(aucun)` | neutre |

**Attributs :** Preferred moves.

**Blocked by:** v2-collectif/19 pour le principe ; chaque ligne est branchée quand son ticket porteur est livré (ouverts : `v2-collectif/15`, `19`, `28a`, 01, 02a, 02b, 03c, 04a, 07a, 09a, 09c, 10a, 10b, 11 ; `v2-mise-en-scene/04`) ; passe après `v2-collectif/22c`.

**Status:** à faire (04/11/2026) : **branchement et mesure des gestes**. La garde de rattachement (premier critère ci-dessous) est passée au ticket `08` (audit de granularité) ; ce ticket garde les deux critères de comportement (fréquence mesurable, réussite inchangée) pour chaque geste, branché quand son mécanisme existe. Les lignes dont le porteur est déjà livré (appels : `v2-collectif/16`, `23` ; passe : `13`, `14`) sont branchées ici, aucun module de `v2engine/` ne lisant encore `Preferred moves` (constat de l'expert du 04/11/2026). Gets Crowd Going tranché le 03/11/2026 : célébrations (`v2-mise-en-scene/04`).

**Point de vigilance :** un geste préféré déplace la fréquence d'un choix, il ne change pas la réussite (règle anti double comptage). Paires contradictoires qui ne peuvent pas coexister : Runs With Ball Often / Rarely, Dives Into Tackles / Does Not Dive Into Tackles, Shoots From Distance / Refrains From Taking Long Shots, Gets Forward Whenever Possible / Stays Back At All Times, Cuts Inside (un côté ou les deux) / Hugs Line, Places Shots / Shoots With Power ; si la base en contient, signaler l'anomalie plutôt que de les additionner. Chaque ligne n'a qu'une implémentation : v2-collectif/19 porte les gestes « porteur », les autres tickets portent les leurs. Composition avec le style et les attributs : règle de `spec.md`. 40 % des joueurs seulement ont des gestes renseignés (ticket 06).

- Repris par le ticket 08, à ne pas livrer ici : les 58 valeurs distinctes de la base sont toutes rattachées à un mécanisme (test qui échoue si une nouvelle valeur apparaît sans rattachement)
- [ ] Pour chaque geste branché : fréquence du choix concerné mesurablement plus haute (ou plus basse) qu'un joueur aux mêmes attributs sans ce geste ; jamais systématique
- [ ] Réussite du geste inchangée à attributs égaux
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
