# 31a: Relevé de départ : zone de centre et présence dans la surface

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026 : « il n'y a pas beaucoup de centres pour le moment dans le moteur et j'aimerais corriger ça avant de continuer le chantier des têtes »). **Priorité :** P1. **Catégorie :** mesure.

**What to build:** relevé, sans changer le moteur, sur 10 matchs du banc (graines d'audit), à chaque instant où un porteur entre dans la zone de centre (`decision.in_cross_zone`) ou s'en approche (à 15 m ou moins, en conduite vers elle) :
- nombre d'entrées dans la zone par équipe et par match, et durée passée dedans ;
- coéquipiers de champ dans la surface adverse à ce moment (distribution 0 / 1 / 2 / 3 et plus), à la lisière (16 à 22 m du but, dans l'axe), et ce qu'ils font (rôle du cerveau : appel, tenir, soutien) ;
- distance du meilleur attaquant à la surface, et position de la ligne du hors-jeu ;
- ce que fait le porteur (centre, passe au sol, conduite, perte) et pourquoi (option de centre absente faute de cible, ou présente mais moins bien valorisée) ;
- centres joués, centres réussis, tirs dans les 5 s après un centre.

**Livrable :** chiffres de départ dans le ticket et `docs/INDICATEURS_V2.md`, script de mesure réutilisable par le `31f` (`scripts/`). Chiffres réels cherchés (centres par équipe, joueurs dans la surface au moment du centre) ; « non trouvé » sinon.

**Attributs :** aucun.

**Blocked by:** rien. **Bloque :** `31b`.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 10 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h** |

Confiance : moyenne. Temps machine, non compté : 10 matchs instrumentés (environ 15 min à 4 processus).

## Acceptance criteria

- [ ] Moteur inchangé (mêmes empreintes à graine fixée avant et après)
- [ ] Chiffres de départ relevés et rapportés ; raison du non-centre ventilée (pas de cible / cible moins bien valorisée)
- [ ] Script de mesure réutilisable ; durée réelle relevée

## Comments
