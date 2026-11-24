# 31d: Appels dans la surface nourris par les attributs

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026 : « il n'y a pas beaucoup de centres pour le moment dans le moteur et j'aimerais corriger ça avant de continuer le chantier des têtes »). **Priorité :** P1. **Catégorie :** exécution.

**What to build:** les appels du `31b` et `31c` deviennent pilotés par les attributs, chacun dans son rôle existant (`docs/CARTE_ATTRIBUTS_V2.md`, règle R1 « un effet, un calcul », sans double comptage ; option A choisie par le propriétaire le 24/11/2026, réserve A1 de l'expert) :
- **lire que le centre devient probable** (Anticipation, délai de réaction existant, précédent du ticket v2-collectif/11 : départ de l'appel en profondeur après une récupération) : ce délai **remplace** le délai d'appel provisoire du `31b` (`off_ball.call_delay_s`, Off the Ball) pour ce déclenchement, il ne s'y ajoute pas ;
- **moment, zone et intensité de l'appel** (Off the Ball, rôle existant « volume, moment et qualité des appels offensifs ») : partir pour arriver lancé quand le ballon part ; choisir la zone libre ou celle dans le dos du défenseur plutôt que la zone attribuée par défaut ; un faible Off the Ball suit la zone attribuée ou court vers le ballon ; l'intensité de la course ne lit que Off the Ball (arbitrage du `12d`) ;
- **reprise de la course après un effort** (Work Rate, rôle existant « efforts sans ballon ») : seulement le fait de repartir après une course déjà faite (centre qui ne part pas, porteur qui revient), sans toucher l'intensité de l'appel.
Si deux attributs se combinent sur un même effet, ce sera par un contexte du registre (ADR 0002), documenté dans la carte.

**Constantes à proposer avant le code :** courbes par attribut (repères 11 / 55 / 99), fenêtre de timing, nombre de répétitions.

**Attributs :** Anticipation (lecture : délai de réaction), Off the Ball (moment, zone, intensité), Work Rate (reprise après un effort) ; rôles existants, option A du propriétaire (24/11/2026).

**Blocked by:** `31c`. **Bloque :** `31f`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : faible (rayon des attributs à vérifier ; découpage possible timing / zone / répétition). Temps machine, non compté : séries de profils (99 contre 11) et série de 50 matchs (environ 1 h 30), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Constantes validées avant le code ; rayon des attributs conforme à la carte, test de rayon à jour
- [ ] Scènes A/B : Anticipation 99 lit le centre et part plus tôt que 11 ; Off the Ball 99 arrive lancé au départ du centre et choisit la zone libre plus souvent ; Work Rate 99 repart plus souvent après une course déjà faite, intensité de l'appel inchangée
- [ ] Série : centres réussis et tirs sur centre relevés ; indicateurs globaux dans le bruit ou expliqués
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; durée réelle relevée

## Comments
