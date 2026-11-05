# 34c: Course du tireur : élan et timing

**Origine (05/11/2026) :** remarques du propriétaire après le ticket 28a : la façon dont le ballon et le joueur arrivent l'un vers l'autre (ballon fort ou arrêté, de face, de côté ou de dos, joueur lancé ou arrêté, bon ou mauvais pied) change la qualité, la puissance et le dosage d'un tir comme d'une passe. Découpage en petits tickets (environ 2 h chacun, mesure comprise), validé par le propriétaire.

**What to build:** Un joueur **lancé** vers le ballon frappe plus fort (l'élan s'ajoute à la puissance du 35a) mais doit ajuster son pas : le timing est plus risqué si le ballon arrive vite ou de côté. Un joueur **arrêté** face au ballon qui vient vers lui frappe moins fort mais plus juste. La vitesse et la direction du tireur au moment de la frappe sont lues dans le moteur (pas de nouvelle donnée). Effets : puissance (35a), difficulté (34b) et part de tirs non cadrés (35b).

**Attributs :** Aucun nouvel attribut (Pace et Acceleration règlent déjà la course, sans effet direct ici) ; Technique amortit le risque de timing comme au 34b.

**Blocked by:** 34b, 35a.

**Bloque :** 36b.

**Status:** à faire (constantes à proposer avant le code)

**Hors de ce ticket :** pied fort et pied faible (`v2-attributs-restants/04a`, qui s'applique ensuite à chacun de ces gestes) ; choix du geste (placée, enroulée, `v2-attributs-restants/10a`).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scènes contrôlées : à même ballon, un tireur lancé frappe plus fort qu'un tireur arrêté ; sur un ballon rapide venant de côté, le tireur lancé a plus de tirs non cadrés
- [ ] Aucun effet de Pace sur la qualité du tir à vitesse de course égale (pas de double comptage)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
