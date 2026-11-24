# 15b3: Lecture du pressing et délai après contrôle (jouer avant le presseur, ou l'attendre)

**Origine :** ticket 15b2 clos sans objet le 17/11/2026 (décision du propriétaire). **Chantier :** `v2-collectif`. **Priorité :** P2. **Catégorie :** décision.

**Constat (15b2) :** après un contrôle, le porteur attend avant sa première décision (`possession.reception_delay_s`, ticket 31b : 2,3 s en moyenne, au moins 3,5 s pour un gardien) ; en construction sous pressing, le presseur est donc à moins de 3 m dans 80 % des décisions (44 sur 55 sur un match). Le porteur attend toujours le presseur, sans le choisir.

**What to build:** en construction sous pressing, un porteur qui lit le pressing (contexte « lecture du pressing », 15b1, même tirage) règle son délai après contrôle : il décide plus tôt s'il voit une passe à jouer avant que le presseur ferme la ligne, ou garde le délai pour fixer le presseur quand l'espace qu'il couvre s'ouvrira à son arrivée. Le délai du 31b reste la règle hors de ce cas.

**Hors de ce ticket :** la fixation pendant la possession (15b2, sans objet) ; le délai hors construction ou hors pressing.

**Attributs :** contexte « lecture du pressing » (15b1), sans nouveau poids ; First Touch garde le délai de base (31b, non relu). Constantes à proposer avant le code : part du délai qu'un lecteur peut retrancher, seuil pour jouer tôt, critère pour attendre.

**Blocked by:** 15b1 (livré). **Bloque :** `v2-realisme/34` (tempo du porteur, qui généralise ce délai hors de la construction sous pressing ; ajouté le 24/11/2026).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code (31b, délai après contrôle) | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 40 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 25** |

Confiance : faible. Hypothèses : le délai après contrôle se règle au moment de la réception, une seule fois ; la projection « presseur retiré des lignes » du 15b2 est réutilisable pour juger l'attente. Au-delà du seuil de 2 h : à réexaminer pour découpage avant le code (jouer tôt d'un côté, attendre exprès de l'autre).
Temps machine, non compté : séries de 50 matchs avant et après ; suite complète.

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code (chiffres réels sourcés ou « non trouvé »)
- [ ] Scène : un bon lecteur sous pressing joue plus tôt quand une passe va se fermer, attend quand l'espace s'ouvrira ; hors pressing, délai du 31b inchangé
- [ ] Statistiques (50 matchs, avant et après) : distance du presseur à la décision, pertes dans son propre tiers, troisièmes hommes, buts et tirs
- [ ] Effet probabiliste, plafond d'écart 99 / 11 ; rayon conforme à la carte, test de rayon à jour
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite complète passée, compte comparé à l'attendu de `CLAUDE.md` ; durée réelle relevée
