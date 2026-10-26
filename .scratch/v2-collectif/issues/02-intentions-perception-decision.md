# 02: Perception, interprétation, décision, exécution

**What to build:** Structurer le cerveau de chaque joueur en quatre temps distincts : **perception** (partenaires, adversaires, espaces et trajectoires qu'il détecte : Vision, Anticipation, Concentration), **interprétation** (menace ou opportunité identifiée), **décision** (action choisie : Decisions, tendances), **exécution** (qualité du geste : attributs techniques et physiques), puis **conséquence** (les autres réagissent). Chaque joueur porte une **intention** explicite (rôle, cible, action), enregistrée dans la trace du match pour la relecture : pourquoi une occasion a été créée, pourquoi une défense s'est désorganisée. Exemple à respecter : un défenseur à 90 en Anticipation détecte la passe en profondeur, mais ne l'intercepte que s'il est assez proche, bien orienté et a le temps d'agir.

**Attributs :** Vision, Anticipation, Concentration (perception) ; Decisions (décision) ; techniques et physiques (exécution).

**Blocked by:** 01.

**Status:** livré (26/10/2026), validé QC

**Point de vigilance :** Vision, Decisions et Passing sont déjà distincts (tickets cerveau 01, 02 et socle 04) : étendre ce principe sans casser l'existant.

- [x] Chaque joueur a une intention lisible à chaque instant dans la trace (rôle, cible, action)
- [x] Voir, choisir et réussir sont trois tirages distincts, testés séparément
- [x] Le rendu V2 peut afficher l'intention d'un joueur (relecture)
- [x] Décision d'architecture écrite (ADR dans `docs/adr/`) avant le code
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [x] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée

## Réalisé (26/10/2026)

- `v2engine/cerveau.py` : perception, interprétation (8 rôles : porteur, appel, soutien, receveur visé, lecture de passe, ballon libre, presseur, replacement), décision ; sortie `Intention` (rôle, action, cible, joueur visé, intensité, raison). `match._step_player` n'exécute plus que l'intention. Décision écrite : `docs/adr/0001-cerveau-joueur.md` ; termes dans `GLOSSARY.md`.
- Trace : intention par joueur et par instant enregistré ; journal des décisions du porteur (`MatchTrace.decisions`).
- API V2 : intentions par segments (nouveau segment au changement de rôle, d'action ou de joueur visé) et journal des décisions. Réponse de 11,4 à 15,1 Mo pour un match.
- Écran V2 : un clic sur un joueur affiche son rôle, son action, la raison et sa dernière décision. Vérifié dans le navigateur sur une API de test.
- Jeu inchangé : empreintes sha256 des traces complètes de 3 matchs identiques avant et après ; mesure de 20 matchs (`scripts.measure_v2 --detail`) identique octet pour octet à la référence. Temps de calcul : 42,0 s contre 43,6 s avant (meilleur de 2).
- Exception assumée (ADR) : le choix du porteur (passer, tirer, conduire) reste dans `match._step_ball`, tracé par le journal.
