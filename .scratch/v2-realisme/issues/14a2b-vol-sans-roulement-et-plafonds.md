# 14a2b: Freinage du ballon en l'air (traînée seule), suppression de MAX_FLIGHT_S, borne de la vitesse de frappe

**Découpé du ticket 14a2 le 26/11/2026** (décision du propriétaire : « 14a2b s'occupera du nettoyage de la dette (MAX_FLIGHT_S et plafond de vitesse), sur une base déjà stabilisée. »). Contexte et constantes : `14a2-roulement-et-trainee.md` ; constats du 02a1 : `14a-freinage-au-sol-calibre.md` (Comments).

**Chantier :** `v2-realisme`. **Catégorie :** physique.

**What to build:**
- en l'air (`z > 0`), `a = k·v²` sans roulement : l'interface `freinage` reçoit l'état en vol là où il compte (pas du moteur, durée de vol `match._launch_aerial`) ;
- supprimer `hauteur.MAX_FLIGHT_S` (durée de vol finie pour toute passe jouable avec la traînée seule) ;
- borner la vitesse totale de frappe √(vh² + vz²) à 35 m/s (repère réel 18 à 35 m/s, 02a1) ; **méthode à faire choisir au propriétaire à l'ouverture** (vz réduit et vol plus court, ou vh réduit).

**Blocked by:** 14a2a. **Bloque :** 14b, 14d ; `v2-collectif/22a`.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs) | 35 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs, suite complète.

## Acceptance criteria

- [ ] Méthode de la borne de vitesse choisie par le propriétaire avant le code
- [ ] Pas de roulement en l'air (test) ; `MAX_FLIGHT_S` supprimé ; durée de vol finie pour toute passe jouable (test) ; vitesse totale de frappe ≤ 35 m/s sur 50 matchs
- [ ] 50 matchs avant/après, écarts au-delà du bruit documentés ; déterminisme ; suite complète ; V1 inchangée
- [ ] Durée réelle relevée

## Comments

**26/11/2026, reprises du 14a2a (expert, facultatif)** : corriger les commentaires `match.py:1026` (« 60 m de course à 30 m/s », environ 77 m désormais) et `hauteur.py:27` (« freinage exponentiel ») ; passer `test_stepped_quantities_follow_the_engine_step` en tolérance absolue `abs=1e-9` ; garder en tête l'écart d'environ ½·dt·v0 entre prévision continue et moteur (A1) si la précision des points de chute compte.
