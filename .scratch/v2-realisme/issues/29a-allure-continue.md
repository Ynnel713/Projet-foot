# 29a: Allure continue : moins de joueurs plantés, plus de trot d'ajustement

**Chantier :** `v2-realisme` (audit de réalisme du propriétaire du 21/11/2026, point « cinématique des pions »). **Priorité :** P1 (effet « translation » visible à l'écran). **Catégorie :** déplacement.

**Constat vérifié (21/11/2026, même audit que le 28a, joueurs de champ, ballon en jeu) :** part du temps par tranche de vitesse.

| Vitesse | Moteur | Metrica |
|---|---|---|
| < 0,5 m/s | 18,1 % | 7,2 % |
| 0,5–2 m/s | 18,9 % | 45,3 % |
| 2–4 m/s | 47,9 % | 35,5 % |
| 4–5,5 m/s | 11,8 % | 8,9 % |
| 5,5–7 m/s | 2,8 % | 2,5 % |
| > 7 m/s | 0,5 % | 0,6 % |

Les accélérations progressives (`movement.accel_tau_s`), le freinage (12a), le virage (12b) et l'orientation (07) sont livrés ; le défaut est ailleurs. Le joueur rejoint sa cible à pleine allure plafonnée puis s'arrête net à 0,1 m (`movement.ARRIVAL_DEADZONE_M`) ; la cible ne bouge qu'aux changements de décision. Il manque le trot lent d'ajustement permanent du réel. Réserves : la vitesse Metrica est une différence finie sur 0,4 s d'un suivi bruité, la vitesse moteur est instantanée ; le ballon mort n'est exclu que côté moteur (côté Metrica, seules les images sans ballon détecté le sont) : les parts sous 0,5 m/s et entre 0,5 et 2 m/s du réel sont biaisées en sens opposés. La référence qui fait foi est `speed_shares` (27b) sur SkillCorner, ballon en jeu ; le tableau ci-dessus ne sert qu'à établir le défaut.

À vérifier au passage (point d'écran, pas de jeu) : la trace de l'écran garde un point toutes les 0,5 s (`api/routers/v2.py`, `_RECORD_EVERY = 5`), ce qui peut lisser les changements de direction plus courts malgré l'interpolation courbe (`v2-correctifs-ecran/04b`).

**What to build:**
1. Allure choisie selon l'urgence : un joueur dont la cible n'est pas urgente (place de référence, couverture lointaine) y va au trot lent plutôt qu'à l'intensité de course pleine ; l'urgence lit la situation existante (`v2-socle/02` intensité de course, `12d` intensité selon le rôle) sans nouvel attribut.
2. Pas d'arrêt sec sur une cible qui suit le jeu : la cible de place suit le ballon de façon continue (petits ajustements), le joueur garde une vitesse d'ajustement au lieu de s'arrêter puis repartir.
3. Mesure au banc : parts de temps par tranche de vitesse (fonction `speed_shares` du 27b), comparées à la référence réelle.

**Attributs :** aucun nouveau (Work Rate et Stamina agissent déjà sur l'intensité, rayons existants : ne pas les relire ici, règle anti double comptage).

**Constantes à proposer avant le code :** allure d'une cible non urgente, seuil d'urgence, lissage de la cible de place. Chiffres réels : distribution de vitesses du 27b et du tableau ci-dessus.

**Blocked by:** 27b (livré).

**Bloque :** 12g (validation de la physique), `v2-collectif/22a` (calibration des volumes de course).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (distance par match, haute intensité, 50 matchs) | 30 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : faible (effet sur la distance parcourue et la fatigue à vérifier ; découpage à examiner avant le code : allure selon l'urgence, puis cible continue). Hypothèses : l'intensité passe toujours par `speed_factor` de `movement.step` ; pas de changement de `movement.py` hors de la loi d'arrivée.
Temps machine, non compté : suite complète ; série de 50 matchs.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code ; découpage examiné
- [ ] Temps à moins de 0,5 m/s et entre 0,5 et 2 m/s dans les quartiles de la référence SkillCorner ballon en jeu (`speed_shares`, 27b), fixée avec le propriétaire avant le code ; cibles indicatives tirées de Metrica : ≤ 10 % et ≥ 35 %
- [ ] Parts à plus de 5,5 m/s inchangées à ± 0,5 point ; distance par match et haute intensité dans les repères du 01c
- [ ] Scène : un joueur sans urgence rejoint une place à 15 m au trot lent ; un joueur en course de couverture urgente garde son allure
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
