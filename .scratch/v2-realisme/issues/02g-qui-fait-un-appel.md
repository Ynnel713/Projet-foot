# 02g: Qui fait un appel, et quand

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les appels doivent être rares, utiles et différenciés). **Catégorie :** décision.

**Constat vérifié :** avant 02f, tous les joueurs de champ appellent ; les tickets livrés `v2-cerveau-joueurs/03` (Off the Ball) et `v2-collectif/16` (appels complémentaires) règlent OÙ appeler, pas QUI appelle.

**What to build:** Choisir les appelants à chaque décision du porteur : rôle autorisé à appeler dans cette situation (avant-centre de profondeur, ailier, latéral offensif, relayeur), espace exploitable par une passe du porteur, nombre maximal d'appels simultanés par situation de jeu. Off the Ball règle le moment (déclenchement plus ou moins tôt) ; aucun autre attribut.

**Attributs :** Off the Ball (moment de l'appel)

**Lien avec l'existant :** complète les tickets livrés `v2-cerveau-joueurs/03` et `v2-collectif/16`, sans les modifier.

**Blocked by:** 02f (Tenir sa position en possession).

**Bloque :** 02h, 13c, 13d.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : la règle provisoire du 02f est remplacée, pas superposée.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** dernier tiers : au plus N appels simultanés ; un défenseur central n'appelle pas en possession installée
- **Comportementaux (profils comparés) :** Off the Ball 99 contre 11 : appels déclenchés plus tôt, à nombre égal
- **Statistiques (séries de matchs) :** 50 matchs : appels par joueur et par poste (repère 5,5 à 19,2 selon le poste, à confirmer au 01c)

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Nombre d'appels simultanés borné par situation (valeurs validées)
- [ ] Effet d'Off the Ball mesurable sur le moment, pas sur le volume
- [ ] Appels par poste rapportés et ordonnés comme au réel (défenseurs centraux les moins nombreux)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 06/11/2026 (réserves de l'expert au 02f, à traiter ici) : **A1** la contre-attaque qui atteint le dernier tiers garde ses appels (`DERNIER_TIERS` prime sur `TRANSITION_OFFENSIVE`) ; **A2** hystérésis : un appelant garde son appel tant que son espace n'est pas atteint, pas d'alternance APPEL / TENIR ; mesurer le taux d'alternance par joueur ; **A3** le joueur désigné par `ball.plan` reste appelant. Test de scène pour chacune. La règle provisoire `PROVISIONAL_RUNNERS` / `HOLD_SITUATIONS` de `cerveau.py` est remplacée, pas superposée.
