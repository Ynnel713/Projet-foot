# 35: Validation du QI foot : un style reconnaissable, pas une note qui gonfle

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur l'intelligence de jeu, points 6 et 7 : qualités qui nourrissent le profil, pièges à éviter). **Priorité :** P2. **Catégorie :** validation.

**Constat vérifié (24/11/2026) :** les briques de l'intelligence de jeu existent ou sont prévues dans des tickets séparés (perception `08a` à `08f`, choix `v2-collectif/33`, scans `08c`, contrôle orienté `v2-collectif/31b`, appels `02g`, `v2-collectif/16`, soutien et décrochage `25c`, `25d`, timing de la passe `v2-collectif/32a`, lignes qui se ferment `33`, tempo `34`, goût du risque `v2-attributs-contextes/05`, lucidité et fatigue `20b`) ; aucune mesure ne vérifie qu'un joueur « intelligent » se distingue par sa lecture, son timing, ses erreurs et son exécution, plutôt que par un gain venu d'une seule note.

**What to build:** une validation par profils, sans réglage : deux joueurs au même poste, l'un haut et l'autre bas en Vision, Decisions, Anticipation et Composure (puis chaque note seule), sur des scènes fixes et en série :
- part de meilleur choix factuel (journal des décisions, `v2-collectif/33`), passes coupées, pertes gratuites, passes vers l'avant réussies, recyclages, gestes risqués tentés ;
- timing : passes en profondeur jouées au départ de l'appel, scans avant réception, orientation ouverte avant la passe (quand les tickets correspondants sont livrés) ;
- **pas de surhomme** : le haut profil se trompe encore parfois, ne lit jamais un adversaire hors de sa perception, et ne voit pas les tirages à venir (tests de garde) ;
- **pas de note unique** : chaque note seule a un effet distinct et borné ; l'effet total se répartit entre lecture, timing, choix et exécution, aucun attribut ne porte tout le gain (rapport par attribut, règle R1 et ADR 0002) ;
- constance : écart entre la première et la dernière demi-heure (Concentration, `v2-collectif/21`, quand livré).

**Attributs :** aucun (mesure).

**Blocked by:** `33`, `34`, `v2-collectif/32a` (volets correspondants seulement si livrés ; la validation peut tourner avant sur ce qui existe). **Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Temps machine, non compté : séries de profils (environ 1 h 30), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Scènes et seuils proposés au propriétaire avant le code
- [ ] Rapport par attribut et par profil, sans réglage ; écarts « surhomme » ou « note unique » signalés au propriétaire en tickets séparés
- [ ] Tests de garde ajoutés : le meilleur profil se trompe encore ; un adversaire non perçu ne pèse pas dans son choix
- [ ] Déterminisme ; suite complète au compte attendu ; durée réelle relevée

## Comments
