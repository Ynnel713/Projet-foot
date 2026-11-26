# 13j: Arbitrage des styles par phase de jeu, budget tactique et couples contradictoires

**Chantier :** `v2-realisme` (audit des styles du coach du 26/11/2026, demande du propriétaire). **Priorité :** P1 (sans arbitrage, un coach à 4 croix devient plus extrême qu'un coach à 2 croix, et les couples contradictoires s'annulent ou s'additionnent au hasard). **Catégorie :** données.

**Constat vérifié :** 13a cumule les styles avec un seul plafond global (`_STYLE_MODIFIER_BOUNDS` de la V1, ±15 %) : rien ne répartit l'effet par phase, rien ne normalise par le nombre de styles cochés, rien ne tranche les couples contradictoires. Base des coachs (`data/Coachs-Simulafoot.xlsx`, 268 coachs hors ligne d'en-tête) : 5 coachs à 1 style, 136 à 2, 116 à 3, 10 à 4, 1 à 5 ; couples contradictoires présents : Défensif + Pressing (30 coachs), Défensif + Offensif (16), Contre-attaque + Possession (16).

**What to build:** Une table « phase × style » et une règle d'arbitrage, produites par la structure de consignes de 13a et tracées par équipe, sans effet de jeu dans ce ticket (les effets arrivent en 13b à 13f, qui lisent cette table).

1. **Phase de jeu** (situations du ticket `v2-collectif/03`) : chaque style n'agit que dans les phases où il a un sens.
   - Avec ballon (possession installée, dernier tiers) : Possession (patience, jeu court, soutien proche) contre Offensif / Contre-attaque (verticalité, passes dans l'espace) ; Défensif y garde deux leviers de 13c (prudence des latéraux, dégagement sous pression dans son tiers).
   - Transition offensive : Contre-attaque (appels immédiats en profondeur, passe verticale rapide) contre Possession (sécuriser le ballon, se redéployer).
   - Sans ballon (défense placée) : Pressing (ligne haute, déclenchement agressif) contre Défensif (bloc compact, axe fermé, surface protégée).
   - Transition défensive : Pressing (contre-pressing, durée du ticket `v2-collectif/10`, `TRIGGER_S`) contre Défensif (repli immédiat vers le bloc) ; Possession y contre-presse aussi, à dose réduite et sur la seule durée du contre-pressing, sans toucher à la hauteur du bloc (« récupère vite après la perte », ticket chapeau `v2-coach-et-gestion-de-match/01`).
2. **Budget tactique** : dans chaque phase, la somme des décalages des styles actifs est normalisée (par le nombre de styles actifs dans la phase, ou par un budget fixe à proposer) ; un coach à 4 croix n'est pas plus extrême qu'un coach à 2 croix, il est plus polyvalent.
3. **Couples contradictoires** dans une même phase : résultat intermédiaire documenté, jamais une annulation à zéro ni une addition. Défensif + Pressing : bloc médian-bas qui ne presse qu'à partir d'une zone déclencheur (moitié de terrain, couloir, passe en retrait : à proposer) ; Défensif + Offensif : bloc bas sans ballon ; avec ballon, projection offensive conservée mais latéraux arbitrés (par exemple un seul latéral projeté à la fois, côté ballon : à proposer) ; Contre-attaque + Possession : la transition offensive choisit selon l'espace (ticket `v2-collectif/11`) avec un biais réduit des deux côtés.

**Principe d'amplitude (propriétaire, 26/11/2026) :** l'impact des styles et de la note du coach reste modéré et réaliste. Un bon coach compense un peu un effectif moyen sans faire de miracle ; un coach moyen n'effondre pas une grande équipe. Le niveau de l'effectif reste le premier déterminant du résultat. Le budget de ce ticket est la borne d'amplitude des styles ; il est proposé en conséquence.

**Attributs :** aucun

**Lien avec l'existant :** complète 13a (structure) ; ne duplique pas la gestion du score (`v2-coach-et-gestion-de-match/02`), qui module ensuite ces valeurs.

**Blocked by:** 13a (Consignes d'équipe : lecture des styles et structure neutre).

**Bloque :** 13b, 13c, 13d, 13e, 13f, 13k, 13i ; `v2-coach-et-gestion-de-match/08`, `10` (ajouté le 26/11/2026, audit de la gestion de match).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : les situations de jeu du ticket `v2-collectif/03` suffisent à découper les 4 phases ; la zone déclencheur Défensif + Pressing est une donnée lue par 13b, pas un mécanisme nouveau.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** décalage cumulé de chaque phase borné par le budget pour tous les coachs ; coach à 2 styles et coach à 4 styles contenant les mêmes 2 : sur les leviers des deux styles communs, décalage du second inférieur ou égal à celui du premier ; Défensif + Pressing : hauteur de bloc entre celle de Défensif seul et celle de Pressing seul, zone déclencheur tracée ; Défensif + Offensif : nombre de latéraux projetés simultanément entre celui de Défensif seul et celui d'Offensif seul ; Possession seul : contre-pressing non nul, inférieur à celui de Pressing seul ; sans coach : neutre
- **Intégration :** mesures identiques à graine fixée

## Acceptance criteria

- [ ] Table phase × style, règle de budget et résultat de chaque couple contradictoire présent dans la base, proposés et validés par le propriétaire avant le code
- [ ] Aucun coach de la base au-delà du budget dans aucune phase (test sur les 268 coachs) ; budget proposé selon le principe d'amplitude
- [ ] Consignes par phase tracées par équipe ; aucun effet sur le jeu dans ce ticket
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
