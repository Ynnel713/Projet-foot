# 11t: Ballon disputé au sol : deux adversaires arrivent ensemble

**Chantier :** `v2-realisme` (audit duels, protection de balle, jeu dos au but, 26/11/2026). **Priorité :** P1 (le duel naît du ballon disputé, pas seulement du porteur pressé). **Catégorie :** exécution.

**Constat vérifié (26/11/2026) :** sur un ballon libre ou une passe limite, le premier joueur qui entre dans le rayon de contrôle le tente seul (`match._contacts` : tri par instant d'entrée, puis distance) ; le second ne dispute rien. Seul le duel d'épaule (11c) met deux adversaires en concurrence, quand ils courent côte à côte dans la même direction. Deux joueurs qui arrivent de face ou en biais à quelques dixièmes de seconde l'un de l'autre ne se disputent pas le ballon : l'élan, l'équilibre et l'engagement ne comptent pas.

**What to build:** quand deux adversaires atteignent le ballon dans une fenêtre courte (valeur validée), un duel au ballon se résout entre eux :
- **gain net** : un joueur contrôle (puis First Touch comme aujourd'hui) ;
- **ballon contré entre les deux** : il repart selon la déviation au contact du 05d (ballon libre, second ballon) ;
- **faute** : d'après la règle du tacle selon l'angle et la vitesse (11d), prudence de surface du 21c1.
Les chances dépendent de l'**avance à l'arrivée**, de l'**élan** (vitesse vers le ballon) et de l'**équilibre** (joueur en contact perdu, 12c, ou en rotation, désavantagé), puis du rapport de force (Strength) et de l'engagement.

**Attributs :** Strength (gagner le contact, rayon existant), Bravery (aller au contact sans retirer le pied : rayon de la carte « accepter le contact risqué », à confirmer avec `17b`), Aggression (fréquence des fautes, inchangée). Anticipation et Acceleration agissent déjà en amont (arriver tôt) : rien de plus ici. Cumul à vérifier dans la carte (R1, ADR 0002).

**Constantes à proposer avant le code :** fenêtre de simultanéité, poids de l'avance, de l'élan et de l'équilibre, partage gain / contré / faute. Chiffre réel : part des duels au sol qui finissent en ballon libre, à sourcer, sinon « non trouvé ».

**Blocked by:** 05d, 11c, 12c, 21c1 (livrés ou à vérifier) ; `11l` (chasseur désigné stable, pour qu'un seul joueur par équipe arrive).

**Bloque :** 04q (validation) ; `v2-collectif/22a` (volume de duels et de fautes).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs appariés) | 30 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : faible (au-delà de 2 h : découpage à examiner avant le code, par exemple résolution et issues, puis Bravery). Hypothèses : point d'insertion dans `match._contacts` et la boucle du ballon libre ; déviation reprise du 05d sans changement.
Temps machine, non compté : suite complète ; série appariée de 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** deux joueurs identiques arrivant au même instant : gain partagé à peu près à parts égales, part de ballons contrés non nulle ; l'un lancé à 6 m/s, l'autre arrêté : le lancé gagne plus souvent ; l'un en contact perdu : il gagne moins souvent.
- **Comportementaux (profils comparés) :** Strength 90 contre 40, Bravery 90 contre 40 : sens attendu, jamais 0 % ni 100 %.

## Acceptance criteria

- [ ] Constantes et chiffre réel validés par le propriétaire avant le code ; découpage examiné
- [ ] Trois issues tracées (gain, contré, faute) et affichées ; toutes présentes sur 50 matchs ; la cause du gain est tracée (avance à l'arrivée ou contact), pour le critère « joueur vif » du 04q
- [ ] Scènes ci-dessus dans le bon sens ; garde du 19c tenue
- [ ] 50 matchs appariés : duels au sol, ballons libres, fautes, pertes rapportés ; écart expliqué
- [ ] Rayon des attributs conforme à la carte ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
