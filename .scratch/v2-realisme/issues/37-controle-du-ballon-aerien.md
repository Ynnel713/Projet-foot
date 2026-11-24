# 37: Contrôle d'un ballon aérien : pied, cuisse, poitrine

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la technique, point 1 « qualité de l'amorti selon le ballon », ballon aérien ou rebondissant). **Priorité :** P1. **Catégorie :** exécution.

**Constat vérifié (24/11/2026) :** un ballon en l'air atteint par un joueur (`v2-hauteur-ballon/03a`, tranche du corps `body_part`) est soit joué de la tête (`15c1`, amorti de la tête compris), soit contrôlé par `possession.attempt_control`, dont la difficulté ne lit que la vitesse au sol et la pression (`possession.control_difficulty`) : la hauteur, la tranche du corps et la vitesse verticale n'y entrent pas. Réussi, le ballon est aussitôt au pied (`ball.z = 0`, `match.py`, contrôle). Un ballon qui tombe du ciel sur la poitrine se contrôle donc comme une passe au sol de même vitesse. Le `26a` exclut explicitement l'amorti de la poitrine et de la cuisse (« après la hauteur des joueurs ») : la hauteur est livrée (`02a`, `03a`).

**What to build:** la **hauteur de contact** (`z_contact` : pied levé, cuisse, poitrine ; tête déjà au `15c1`) et la **vitesse de descente** (ballon qui retombe d'un long ballon, rebond haut) deviennent un **terme de la difficulté du contrôle du `26a`**, pas un tirage distinct : le contrôle aérien a la même issue continue (distance et direction du ballon après contact, le raté restant la queue de la distribution). Technique compense la difficulté **une seule fois par réception**, dans le calcul du `26a` (la gêne aérienne s'ajoute à la gêne du ballon dur avant cette compensation, jamais une seconde compensation). Seul ajout propre à ce ticket : un court délai avant de jouer selon la hauteur (poitrine plus lent que le pied). Sous pression (Composure, R3) comme aujourd'hui. Si le `26a` intègre déjà la hauteur à sa livraison, ce ticket se réduit à vérifier les scènes et au délai selon la hauteur.

**Hors de ce ticket :** volée et demi-volée (`v2-collectif/34d`) ; duel aérien (`15b`) ; tête (`15c`).

**Attributs (ADR 0002, poids à proposer) :** aucun effet nouveau : First Touch et Technique agissent par le calcul du `26a`, une fois par réception (R1). Balance : non (son rayon est l'après-contact, `12c`).

**Blocked by:** `26a` (issue continue du contrôle) ; `v2-hauteur-ballon/03a`, `15c1` (livrés).

**Bloque :** `39`, `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : `atteinte.body_part` ne distingue que pied, corps, tête et mains (pas de cuisse ni de poitrine) : la gêne se lit sur la hauteur de contact `z_contact` (déjà tracée, `ReceptionEvent.ball_z_m`), sans nouvelle tranche ; la gêne entre dans la difficulté du `26a`. Au-dessus de 2 h de peu : découpage à examiner au lancement si le `26a` n'a pas déjà la hauteur. Temps machine, non compté : série de 50 matchs (environ 40 min), suite complète (environ 20 min).

## Tests

- **Scènes :** même joueur, même vitesse horizontale : distance du ballon après contact plus courte au sol qu'à hauteur de poitrine, elle-même plus courte que sur un ballon qui retombe vite ; Technique 99 contre 11 : écart plus grand sur le ballon aérien qu'au sol ; ballon aérien dur reçu en course : un seul terme Technique dans la dispersion (test de rayon).
- **Statistiques (50 matchs) :** contrôles aériens par match et par hauteur, distance après contact par hauteur, pertes après un long ballon.

## Acceptance criteria

- [ ] Constantes produit (gêne selon la hauteur et la descente, délai selon la hauteur) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Hauteur de contact et distance après contact tracées
- [ ] Scènes ci-dessus
- [ ] Réussite des longs ballons (`v2-collectif/15a`) comparée avant / après et expliquée
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
