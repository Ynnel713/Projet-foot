# 18i: Passe précise coupée trop souvent, même courte

**Chantier :** `v2-realisme`. **Catégorie :** exécution, défense.

**Origine :** ticket 18h (12/11/2026, 12 matchs, moteur après 18g). Une passe PRÉCISE (tirage de `possession.pass_aim` réussi) n'est reçue par un coéquipier que dans environ 85 % des cas, quelle que soit sa longueur : courte 85,4 %, moyenne 85,3 %, longue 86,0 %. Les échecs viennent des coupes (adversaire qui touche le ballon le premier : table du 18g, plus environ 5 % de coupes imprévues). Réel indicatif (toutes passes, précises ou non) : courte 89,4 %, moyenne 87,1 %, longue 51,7 % (Premier League 2024-25, Total Football Analysis d'après FBref). Une passe courte précise est presque jamais coupée dans le réel.

**What to build :** Trouver pourquoi une passe courte précise est coupée aussi souvent qu'une longue (placement et course des défenseurs pendant la passe, `anticipation.pass_readers`, contacts du ballon avec un joueur proche du passeur, choix de passes dans le trafic) et corriger le mécanisme. Remesurer ensuite la table de coupe du 18g et l'indicateur de calibration de la passe.

**Hors de ce ticket :** conséquence de la passe ratée (18h) ; calibration finale des passes (`v2-collectif/22a`).

**Attributs :** Anticipation, Positioning, Passing (aucun rôle nouveau).

**Blocked by :** 18h.

**Bloque :** `v2-collectif/22a`.

**Status :** à faire (diagnostic d'abord ; constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 1 h |
| Développement | 30 min |
| Tests | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 30** |

Confiance : faible (cause à trouver). À examiner pour découpage après le diagnostic. Temps machine, hors total : diagnostics et séries de 50 matchs, suite complète.

## Acceptance criteria

- [ ] Cause des coupes de passes courtes précises identifiée et chiffrée (diagnostic)
- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Réussite par longueur (courte, moyenne, longue) mesurée avant/après sur 50 matchs, comparée au réel
- [ ] Table de coupe du 18g remesurée ; indicateur de calibration de la passe sous 5 points par tranche
- [ ] Suite complète comparée à l'attendu de `CLAUDE.md`

## Comments

**12/11/2026, reprise du 18h.** Corriger aussi la docstring de `possession.pass_aim` (« déviée de 10 à 25 % » : 25 à 50 % depuis le 18h, réserve facultative A2 de l'expert).
