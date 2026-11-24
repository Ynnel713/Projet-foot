# 31b: Déclenchement de l'attaque de la surface et nombre d'attaquants

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026 : « il n'y a pas beaucoup de centres pour le moment dans le moteur et j'aimerais corriger ça avant de continuer le chantier des têtes »). **Priorité :** P1. **Catégorie :** décision.

**What to build:** une règle de déclenchement lue par le cerveau (`cerveau.interpret`, rôle des coéquipiers du porteur) :
- **quand** : un coéquipier a le ballon dans la zone de centre, ou s'en approche en conduite à une distance à fixer, ou va la recevoir (passe en cours vers un receveur dans la zone) ;
- **combien** : nombre d'attaquants qui partent dans la surface (base, plus un quand l'équipe a le nombre, borne), comptés à part des appelants ordinaires (`CALLER_CAP`) ou dedans : à trancher ;
- **qui** : priorité par poste et position (attaquant axial, ailier opposé, milieu offensif le plus proche), jamais les joueurs de la garde (`31e`), jamais le porteur ni le gardien.
Rôle nouveau du cerveau (par exemple « attaque de la surface »), tracé. Les cibles précises sont au `31c` (ici : provisoire, la surface la plus proche) et les attributs au `31d` (ici : délai de départ existant, `off_ball.call_delay_s`).

**Constantes à proposer avant le code :** distance d'approche de la zone (indicatif : 15 m) ; nombre de base et borne (indicatif : 2, jusqu'à 3) ; priorité des postes ; durée de vie du déclenchement après la sortie du porteur de la zone.

**Attributs :** aucun rôle nouveau (délai d'appel existant : Off the Ball).

**Blocked by:** `31a`. **Bloque :** `31c`, `31d`, `31e`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : faible (interaction avec `CALLER_CAP`, `02f` tenir et `02g` appel à étudier au lancement). Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Constantes validées avant le code
- [ ] Scène : ailier avec le ballon dans la zone de centre : le nombre validé d'attaquants part vers la surface ; porteur hors zone et loin : personne
- [ ] Série : coéquipiers dans la surface au moment d'un centre possible et centres par équipe relevés (avant / après), buts encaissés en transition rapportés
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; durée réelle relevée

## Comments
