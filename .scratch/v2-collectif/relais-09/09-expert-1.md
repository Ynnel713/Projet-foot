Ticket : v2-collectif/09
Empreinte : 45764bb1141c25e74f72fb5b0f468a8f2df95cbb45b70f9d694ad602f6688892
Verdict : REJECTED
Résumé : Les deux mesures confirment deux défauts tactiques du scénario de référence : le joueur qui compense quitte la place dans 33,7 % des cas juste après l'arrivée de l'ailier, et la compensation tombe à 0 % dès que le ballon est joué vers l'ailier.

## Identification
- Périmètre examiné :
  - `v2engine/defense.py` : `_compensate`, `_rank`, `_willing`, la passe adverse en vol dans `update`, `arrival_time_s`.
  - `v2engine/cerveau.py` : rôle pendant la passe adverse en vol, action « compenser ».
  - `tests/test_v2engine_compensations.py` : 13 tests.
  - `tests/test_v2engine_rayon_attributs.py`.
- Dépendances lues : `bloc.reference`, `bloc.placement_error` (erreur `_POSITIONING_ERROR_M`), `movement.accel_tau_s` et `max_speed_mps`, `anticipation.reaction_delay_s`.
- Dossier reçu :
  - Suite complète : 2 262 passés, 13 désélectionnés.
  - Mesures sur 20 matchs à partir de `7a94d64`.
  - Diagnostic des rôles sur 4 matchs.
  - Déterminisme : même empreinte de trace sur deux exécutions.
  - Vérifications V1 et V2 faites hors dépôt (`verif_09.py`, lu). L'empreinte du dépôt est la même avant et après.

## Analyse du réalisme
- Ce qui progresse :
  - Un rôle défensif est attribué pendant 98,8 % de la possession adverse, contre 56,6 % avant. Cela inclut les passes en vol (réserve A2 du ticket 07).
  - La distance du marqueur à Marking 99 baisse de 8,05 à 7,48 m.
  - La hiérarchie milieu défensif, puis central, puis latéral opposé est respectée, comme le délai d'arrivée et l'effet des attributs (Teamwork tiré au hasard, Anticipation, Positioning).
  - Le milieu défensif compense 7,7 % du temps (C6 tenu). Le temps de calcul augmente de 13,5 %. Passes, tirs et buts sont stables.
- Ce qui ne va pas, et touche au cœur du ticket :
  - **La compensation se défait au moment critique.**
    - V1 (place vide, ailier sans ballon) : un tiers des compensateurs lâchent la place 0,0 à 0,6 s après l'arrivée de l'ailier et retournent à leur propre place, alors que le latéral est toujours absent.
    - V2 (ailier servi) : la compensation disparaît dès le départ de la passe. Le presseur est le plus souvent le MC, l'ancien compensateur seulement dans 20 % (vol) et 35 % (ballon reçu) des ticks.
  - Sur le terrain, cela donne l'ailier qui reçoit dans le couloir du latéral monté, sans personne à la place, alors que le milieu défensif y était une seconde plus tôt. C'est exactement ce que le ticket devait empêcher.
  - C3 (tirs de contre de 3,45 à 4,5 par match) : réserve déjà acceptée par le propriétaire et renvoyée au ticket 10. Je n'y reviens pas.

## Vérifications
- **Calcul (a), fait à la main avant mesure.**
  - Le titulaire est gardé si `d/v + tau_i <= d_att/v_att + tau_att + 0,3` (`defense.py:245-247`). `arrival_time_s` (`defense.py:110-112`) compte le temps de montée en vitesse même quand la distance est nulle.
  - Attaquant arrivé (d_att = 0), profils égaux (Pace 60, donc 31,3 km/h = 8,7 m/s) : le compensateur est retiré s'il se tient à plus de 0,3 × 8,7 = 2,6 m de la place.
  - Or l'erreur de Positioning d'un joueur moyen est tirée uniformément entre 0 et 5 m (`bloc.py:215`).
- **V1, mesure (fait observé)** : 1 000 tirages, l'ailier arrive à chaque fois.

  | Après l'arrivée de l'ailier | Rôle de compensation encore attribué | Un joueur domicile à moins de 5 m de la place |
  |---|---|---|
  | +0,5 s | 62,6 % | 96,2 % |
  | +1,0 s | 62,5 % | 90,5 % |
  | +2,0 s | 62,5 % | 68,7 % |

  - Rôle perdu alors que le latéral est toujours absent : 33,7 %.
  - Distance du compensateur à la place au moment du retrait : minimum 2,62 m, médiane 3,34 m. Le minimum tombe exactement sur le seuil calculé de 2,6 m : le mécanisme est confirmé.
  - La fréquence est un peu sous ma prédiction (40 à 60 %), parce que le compensateur continue d'avancer vers son point visé et que certains tirages tombent sous le seuil.
  - Écart de protocole sans effet sur la conclusion : les défenseurs qui ont un rôle suivent leur cible, ceux qui n'en ont pas regagnent leur place dans le bloc, ce qui est fidèle à `REPLACEMENT`.
- **Lecture du code (b)** :
  - Le presseur reçoit toujours `mate = holder.name` (`defense.py:303`), et `_compensate` exclut des menaces tous les joueurs déjà pris en charge (`marked`).
  - Le porteur n'est donc jamais une menace. La ligne `threats = [holder if p.name == holder.name else p ...]` ne sert jamais, contrairement à la docstring (« porteur compris ») et au fichier ticket (« Le porteur compte parmi les menaces »).
- **V2, mesure (fait observé)** : 200 tirages, Teamwork 99 au milieu défensif.
  - Passe en vol, 7 326 ticks : compensation 0,0 %. Presseurs : MC 5 803 ticks, MDC 1 523.
  - Ailier porteur, 1 980 ticks : compensation 0,0 %. Le presseur est l'ancien compensateur dans 35,3 % des ticks.
  - Limites : l'ailier est immobile pendant le vol et les défenseurs sans rôle aussi. Cela ne change pas le résultat : la compensation est à 0 % par construction, puisque la seule menace proche est le porteur.
- **Limites générales** : ce sont des scènes synthétiques. La fréquence en match n'est pas mesurée. Mais le scénario mesuré est le scénario de référence du ticket, et les deux mécanismes sont démontrés par le code et par la mesure.
- **Contrôle qualité** : verdict BLOQUÉ de son côté, rendu indépendamment.

## Anomalies
A1 [BLOQUANT] — Le compensateur lâche la place dès que l'ailier y arrive.
- Preuve : `defense.py:245-247`, avec `arrival_time_s` qui compte la montée en vitesse à distance nulle. V1 : 33,7 % de retraits, distance minimale au retrait 2,62 m.
- Règle violée : « il rend la place dès que le joueur absent revient à moins de 5 m » (constante validée).
- Conséquence : à +2 s, plus aucun défenseur à moins de 5 m de la place dans 31 % des cas, avec l'ailier dedans.
- Correctif recommandé : garder le titulaire tant que le trou existe et qu'il est à moins de `HOLE_FILLED_M` de la place, quel que soit le temps d'arrivée de l'attaquant. La règle des 0,3 s ne s'appliquerait qu'à un titulaire encore en route.
  - C'est local, le comportement reste inchangé avant l'arrivée, et c'est conforme à la règle validée.
  - Option écartée : retirer le temps de montée en vitesse à distance quasi nulle. Cela corrige le symptôme mais reste fragile face à l'erreur de Positioning (jusqu'à 8 m pour un Positioning bas).
- Test à ajouter : la vérification V1 en test (`_run` prolongé de 2 s, sans-rôle vers leur place), avec le rôle attribué dans au moins 95 % des tirages à +2 s tant que le latéral est absent.

A2 [BLOQUANT] — L'ailier servi ou en vol vers la place n'est jamais une menace, donc la compensation tombe à 0 %.
- Preuve : `defense.py:303` (presseur avec `mate = holder.name`), puis `marked` dans `_compensate`. La ligne qui réinjecte le porteur ne sert jamais. V2 : 0,0 % en vol comme ballon reçu.
- Conséquence : dans le scénario de référence joué par une passe à l'ailier, la place du latéral est abandonnée dès le départ de la passe. Le code contredit ce que la docstring et le ticket déclarent.
- Correctif recommandé : calculer `marked` à partir des seuls rôles `MARQUAGE`. Le porteur, ou le receveur à son point de réception, reste alors une menace même s'il est pressé.
  - Alternative : décider que le pressing et la couverture suffisent face au porteur. Il faudrait alors retirer la ligne qui ne sert pas, corriger la docstring et le ticket, et obtenir l'accord explicite du propriétaire sur le scénario de référence. Je ne la recommande pas : V2 montre que le presseur est le plus souvent le MC, venu de l'axe, et que la place reste vide.
  - Après correction, remesurer C6 (au plus 20 %), C3 et les tacles.
- Test à ajouter : V2 en test, avec la compensation maintenue dans au moins 90 % des ticks, ou l'ancien compensateur devenu presseur.

A3 [RÉSERVE] — Les niveaux de cascade sont remis à zéro sur un tick de ballon libre sans receveur.
- Preuve : `defense.py:266` puis `return` (`defense.py:270`).
- Conséquence : un compensateur de niveau 2 redevient de niveau 1, ce qui autorise un troisième niveau. Rare et bref.
- Correctif : rétablir `self.levels = levels` avant ce `return`.
- Test : un tick de ballon libre entre deux mises à jour garde `levels`.

A4 [RÉSERVE] — Le test C1 (`_run`) s'arrête à l'arrivée de l'ailier et ne fait bouger que les compensateurs. Le 96,2 % de C1 surestime donc la tenue réelle de la place, ce qui explique qu'A1 et A2 soient passés inaperçus.
- Correctif : couvert par les tests proposés en A1 et A2.

## Recommandation finale
- **Décision** : REJECTED. A1 et A2 sont démontrés, par le code et par la mesure, sur le scénario de référence du ticket. A1 viole une règle validée par le propriétaire. A2 contredit le comportement que le ticket et la docstring déclarent. Les autres apports, en particulier la réserve A2 du ticket 07 (passe en vol) et l'effet des attributs, sont sains.
- **Actions obligatoires avant nouvelle revue** :
  1. Corriger A1 et A2 dans `v2engine/defense.py`.
  2. Ajouter les tests V1 et V2.
  3. Remesurer sur 20 matchs (C3, C5, tacles) et sur 4 matchs (C4, C6).
  4. Corriger la docstring et le fichier ticket selon le choix fait pour A2.
- **Facultatif** : A3.
- **À surveiller** : la part de temps en compensation (C6) et les tirs de contre (C3) après la correction d'A2, qui élargit les déclenchements.
- Fichiers : C:\Users\omariani\OneDrive - CY Cergy Paris Université\Documents\OLYV\Projet foot\simulafoot\v2engine\defense.py ; C:\Users\omariani\OneDrive - CY Cergy Paris Université\Documents\OLYV\Projet foot\simulafoot\tests\test_v2engine_compensations.py
