# 11: Centres variés

**What to build:** Le ticket 01 crée le centre et le duel aérien. Ce ticket en fait un geste **varié et cohérent** : un centre n'est pas toujours le même ballon dans la surface.

1. **Types de centres** : enroulé (en arc vers le second poteau ou le point de penalty), tendu « au cordeau » (rapide, dans les 6 mètres), en retrait (depuis la ligne de fond vers la lisière), au ras du sol.
2. **La situation décide** : position du centreur (près de la ligne de fond : retrait ou ras du sol ; dans le couloir : enroulé ou tendu), position des attaquants, des défenseurs et du gardien, grands gabarits à la finition (jeu aérien du ticket 01). Crossing règle la qualité d'exécution ; Decisions choisit ; Flair ajoute les centres risqués ; les gestes préférés ne biaisent que la fréquence.
3. **Suite du centre** : tête, reprise du pied, gardien qui capte ou claque (ticket 28), défenseur qui dégage (ballon mort du ticket 29). Le mode de ballon (29) affiche le type.

**Attributs :** Crossing, Decisions, Flair, Vision ; gestes préférés en penchants (ticket 05).

**Blocked by:** 01 (centres et jeu aérien), `v2-collectif/28b` (issue du tir), `v2-collectif/29` (mode de ballon, livré) ; `v2-realisme/23b` (erreur d'exécution continue du centre, ajouté le 10/11/2026).

**Status:** à faire (constantes à proposer avant le code)

**Origine (03/11/2026) :** demande du propriétaire (centres enroulés, au cordeau, en retrait ; décision Q10).

**Chiffres réels :** centres par match, part de centres réussis, buts sur centre : définitions variables, **non trouvés de façon fiable, à sourcer**. Sans chiffre, chaque type apparaît au moins une fois sur 50 matchs et aucun ne domine.

**Point de vigilance :** variété artificielle interdite (règle de `docs/PLAN_V2.md`) : le type doit dépendre de la situation, sinon le ticket est refusé.

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Test de cohérence (scènes fixes) : le retrait est plus fréquent depuis la ligne de fond quand un attaquant arrive à la lisière ; le centre tendu est plus fréquent quand l'attaquant se présente dans les 6 mètres ; l'enroulé est plus fréquent depuis le couloir
- [ ] Crossing élevé : plus de centres qui atteignent un coéquipier, à situation égale
- [ ] Chaque type est tracé avec son mode de ballon et affiché
- [ ] En match (50 matchs, graine d'audit) : répartition des types, diversité des buts sur centre mesurée (zone, type, issue)
- [ ] Rayon des attributs conforme à la carte, sans double comptage
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Limite d'angle du 14a2b (27/11/2026)

**Limite d'angle de départ héritée du `v2-realisme/14a2b` (note du propriétaire, 27/11/2026)** : La limite de 45° (vz <= vh * tan(45°)) imposée au 14a2b est un garde-fou moteur contre les trajectoires aberrantes. Elle interdit les lobs verticaux. Lors de l'implémentation des gestes spécifiques (Lob au 10a, centres au 11), cette limite devra être contournée. Un geste explicitement identifié comme 'Lob' ou 'Chandelle' devra avoir l'autorisation de dépasser cette limite d'angle pour reproduire la réalité du terrain. Ici : un centre explicitement identifié comme 'Chandelle' (ballon haut dans la surface) doit pouvoir partir au-delà de 45° ; les autres types de centres restent bornés.
