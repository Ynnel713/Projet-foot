# 10m: Repli du bloc à la perte : le centre de l'équipe recule et le bloc se resserre

**Chantier :** `v2-realisme` (audit des transitions du 26/11/2026, demande du propriétaire, ticket proposé « T4 »). **Priorité :** P1 (presque tous les buts du moteur viennent d'une transition). **Catégorie :** placement.

**Constat vérifié :**
- `v2-collectif/10` (livré le 03/11/2026) donne à chaque joueur sa réaction à la perte (contre-pressing proche, deux plus reculés gardés dans l'axe, repli des autres vers leur place du bloc). Mais le centre de l'équipe ne recule pas, il avance encore après la perte. Convention du banc (`scripts/v2_indicators.py`, `_retreat`) : vitesse de recul positive = vers son propre but. Mesures du moteur à deux dates : −0,76 m/s à la clôture du 10 ; dernière mesure du banc, latence 1,6 s, vitesse de recul −0,25 m/s, bloc reformé en 2,9 s (`docs/INDICATEURS_V2.md`, indicateur 7). Valeur réelle : non trouvée.
- Cause identifiée au 10 : la place de référence du bloc monte avec le ballon pendant la transition. Une règle « pas de montée » a été essayée puis retirée (03/11/2026) : elle faisait chuter le hors-jeu de 2,0 à 0,69 par match.
- La réserve a été renvoyée à la calibration `v2-collectif/22b` (« recul du bloc »). Or c'est un défaut de mécanisme, pas une constante à régler.
- Rien ne resserre le bloc en largeur à la perte : le coulissement (10e) ne vaut qu'en défense placée.
- Origine des buts (19e, 20 matchs) : 95 % viennent d'un ballon gagné à l'adversaire, à 3 s du but en médiane.

**What to build:** À la perte, la place de référence du bloc vise une hauteur et une largeur de repli au lieu de suivre le ballon :
- hauteur : en retrait du ballon d'une profondeur à proposer ;
- largeur : resserrée vers l'axe, avec la même part que le coulissement de 10e.

Le bloc y revient progressivement, jusqu'à la défense placée. La ligne garde sa règle de hors-jeu : elle remonte dès que le ballon est contenu (porteur pressé, passe en retrait), et le hors-jeu ne doit pas retomber sous 2 par match.

Hauteur et largeur cibles sont des paramètres d'équipe, sans seconde mécanique. Ils sont modulés plus tard par :
- le style (13c repli immédiat, 13b contre-pressing, arbitrage 13j) ;
- le score (`v2-collectif/21`, coach `02`) ;
- la capacité restante (20e).

**Attributs :** aucun nouveau. Work Rate garde son rayon (intensité du repli, ticket 10) ; Teamwork garde le sien (écart toléré à sa place).

**Lien avec l'existant :** complète `v2-collectif/10` (livré, non modifié) et `10e`. Reprend le mécanisme de la réserve « recul du bloc » du 10. Le 22b garde le contrôle chiffré de cette réserve.

**Blocked by:** 10e (Coulissement) ; 01f (Fabrique de scènes de test).

**Bloque :** 10n ; `v2-collectif/22b`.

**Dépendance non réciproque :** 01f (livré) n'est pas modifié ; sa ligne « Bloque » ne cite pas 10m.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : la place de référence du bloc (`bloc.py`) peut recevoir une cible de transition sans toucher à la ligne du hors-jeu ; l'essai « pas de montée » du 10 sert de point de départ.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs avant/après.
Au-delà de 2 h : à examiner pour découpage avant le code (par exemple hauteur d'un côté, largeur de l'autre).

## Tests

- **Unitaires (scène contrôlée) :** perte au milieu de terrain, bloc haut et large : 3 s après, centre de l'équipe plus bas et largeur plus faible qu'au moment de la perte ; ballon contenu (porteur pressé) : la ligne remonte
- **Statistiques (séries de matchs) :** 50 matchs avant/après, mêmes graines : latence, vitesse de recul, bloc reformé, largeur du bloc 3 s après la perte, hors-jeu par match, tirs de contre après récupération, buts issus d'une récupération

## Acceptance criteria

- [ ] Constantes produit (profondeur de repli, resserrement, condition de remontée) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Vitesse de recul du centre de l'équipe (convention du banc : positive = vers son but) positive, ou au minimum nettement plus élevée qu'avant (−0,25 m/s à la dernière mesure), et bloc reformé plus vite (seuils proposés avant la mesure)
- [ ] Largeur du bloc 3 s après la perte inférieure à celle du moment de la perte
- [ ] Hors-jeu non dégradé : valeur actuelle relevée avant le code (1,6 par match à la clôture du 10), puis au moins 2 par match (seuil de la réserve A3 du 10) ou, à défaut, pas de baisse par rapport à la valeur relevée
- [ ] Tirs de contre après récupération et part des buts issus d'une récupération en baisse ou stables (sens mesuré, intervalle de confiance)
- [ ] Hauteur et largeur cibles exposées comme paramètres d'équipe, lisibles par 13j, 21 et 20e
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
