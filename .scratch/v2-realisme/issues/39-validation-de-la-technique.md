# 39: Validation de la technique : des joueurs techniques reconnaissables, sans autoroute

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la technique, point 5 « comment les joueurs techniquement supérieurs doivent se voir en match », point 6 « exploitation par les coéquipiers » et « équilibre des statistiques », priorité 3). **Priorité :** P2. **Catégorie :** validation.

**Constat vérifié (24/11/2026) :** le banc mesure déjà le risque de conduite par tranche de Dribbling (`04c`), le temps par possession et par type de réception (`07d`, indicateur n° 27) et les pertes après contact (`11i`) ; le `04n` prévoit la variété des gestes du duel. Aucune mesure ne compare des profils techniques par **situation** (petits espaces sous pressing, un contre un, conduite en transition, dernier tiers), ni ne vérifie que l'espace créé par un dribble ou un contrôle orienté est ensuite exploité.

**What to build:** une validation par profils, sans réglage : deux joueurs au même poste, l'un haut et l'autre bas en First Touch, Dribbling, Technique (puis Agility, Balance, Composure, chacune seule), en scènes fixes et en série :
- **petits espaces et pressing** : réception avec au moins deux adversaires à moins de 5 m : part des ballons gardés 3 s plus tard, part des sorties par un contrôle orienté (`36`) ou un geste court, part des dégagements longs ou en retrait forcés ;
- **un contre un** : duels tentés et gagnés, défenseurs déséquilibrés (`04o`), fautes subies, et ce qui suit (action dans les 5 s : passe au joueur libéré, tir, perte) ;
- **conduite en transition** : pertes par 100 m conduits, vitesse balle au pied (`04d`, A2), touches trop longues (`04f`) ;
- **dernier tiers** : temps entre la réception et la passe ou le tir, part des réceptions qui ouvrent un angle de tir ou de passe ;
- **exploitation** : après une élimination, part des actions où un coéquipier libéré reçoit (lignes qui s'ouvrent, `33`) ; si elle est nulle ou faible, ticket séparé pour les appels déclenchés par le décalage ;
- **pas d'autoroute** : le meilleur profil rate encore des gestes et des contrôles (seuil maximal de réussite), le surnombre le reprend, et les dribbles tentés et réussis par match restent dans le repère réel (s'il est trouvé) ; le moins bon n'est pas puni à chaque geste (seuil minimal) ;
- **pas de note unique** : l'effet se répartit entre réception, geste, conduite et décision (rapport par attribut, R1, ADR 0002).

**Attributs :** aucun (mesure).

**Blocked by:** `04n`, `04o`, `36`, `37`, `38` (volets correspondants seulement si livrés ; la validation peut tourner avant sur ce qui existe). **Bloque :** rien (écarts signalés en tickets séparés).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : les indicateurs réutilisent le journal des événements (`19b`) et les traces de réception ; scènes par la fabrique `tests/scenes.py`. Temps machine, non compté : séries de profils (environ 1 h 30, en tranches de moins de 1 h), suite complète (environ 20 min).

## Acceptance criteria

- [ ] Scènes, seuils (réussite maximale du meilleur, minimale du moins bon) et repères réels (sourcés ou « non trouvé ») proposés au propriétaire avant le code
- [ ] Rapport par situation, par attribut et par profil, sans réglage ; écarts signalés au propriétaire en tickets séparés
- [ ] Tests de garde ajoutés : le meilleur profil rate encore ; deux défenseurs serrés reprennent le ballon plus souvent qu'un seul
- [ ] Indicateurs ajoutés au banc et définis dans `docs/INDICATEURS_V2.md`
- [ ] Déterminisme ; suite complète au compte attendu ; durée réelle relevée

## Comments
