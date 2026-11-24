# 31e: Garde de sécurité derrière le ballon pendant l'attaque de la surface

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026 : « il n'y a pas beaucoup de centres pour le moment dans le moteur et j'aimerais corriger ça avant de continuer le chantier des têtes »). **Priorité :** P1. **Catégorie :** décision.

**What to build:** pendant l'attaque de la surface (`31b`), l'équipe garde derrière le ballon un nombre minimal de joueurs de champ (défenseurs centraux et un milieu récupérateur), qui ne partent jamais dans la surface et tiennent une position qui couvre les attaquants adverses restés haut (contre après un centre contré, dégagé ou capté). Le latéral opposé ne monte pas en même temps que le latéral du côté du ballon. Lien : `defense.REST_DEFENDERS` (2, fixe, aujourd'hui en possession installée seulement) ; le `09g` (à faire) remplacera ce nombre fixe par « attaquants adverses restés haut plus un » : ce ticket s'y branche sans le devancer.

**Constantes à proposer avant le code :** nombre minimal de joueurs gardés (indicatif : deux défenseurs plus un milieu), postes prioritaires, position (distance derrière le ballon, couverture de l'attaquant adverse le plus avancé).

**Attributs :** Teamwork (rôle existant : tenir sa place ; l'indiscipliné peut monter quand même).

**Blocked by:** `31b`. **Bloque :** `31f`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Constantes validées avant le code
- [ ] Scène : attaque de la surface déclenchée : jamais moins que le minimum validé derrière le ballon ; contre adverse après un dégagement : la garde couvre l'attaquant le plus avancé
- [ ] Série : buts et tirs encaissés dans les 15 s après un centre (avant / après le `31b`), sans hausse significative
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; durée réelle relevée

## Comments
