# 13: Valeur future d'une passe

**What to build:** Le porteur n'évalue plus une passe seulement par sa probabilité de réussite : il estime ce qu'elle **prépare** (solutions suivantes du receveur, progression, bloc adverse attiré). Une passe latérale peut être la meilleure parce qu'elle attire le bloc avant de trouver un joueur entre les lignes. Pas de ping-pong : l'orientation du contrôle, la pression, le temps disponible et la qualité des solutions comptent.

**Attributs :** Vision, Decisions, Passing.

**Blocked by:** 06.

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** le ping-pong a été corrigé au ticket socle 06 par le temps de réception : ce ticket ne doit pas le réintroduire.

- [ ] À situation égale, une passe qui ouvre une solution suivante est choisie mesurablement plus souvent qu'une passe sûre sans suite
- [ ] Les acquis du rythme tiennent (ticket socle 06 : 15-17 passes par minute, 3-5 passes par possession)
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
