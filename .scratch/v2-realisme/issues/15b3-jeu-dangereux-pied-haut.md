# 15b3: Jeu dangereux : pied haut contre une tête

**Chantier :** `v2-realisme` (découpe du `15b`, facultatif, validée par le propriétaire le 24/11/2026). **Priorité :** P3. **Catégorie :** exécution.

**Constat vérifié :** aucun jeu dangereux ; le pied ne joue le ballon que jusqu'à la hanche (`atteinte.FOOT_SHARE`).

**What to build:** un joueur qui joue au pied un ballon à hauteur de tête d'un adversaire tout proche (duel du `15b1`) commet un jeu dangereux : coup franc indirect pour l'adversaire. Constantes à proposer avant le code.

**Blocked by:** `15b1`. **Bloque :** rien.

**Status:** clos sans objet (24/11/2026, décision du propriétaire : « Clore sans objet ») — la situation n'arrive pas dans le moteur ; à rouvrir avec un futur ticket de volées hautes ou de têtes plongeantes

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 15** |

Confiance : faible (coup franc indirect hors hors-jeu à vérifier dans `restart.py`).

## Acceptance criteria

- [ ] Constantes validées avant le code (sans objet : aucune constante proposée)
- [ ] Scène : pied haut près d'une tête sifflé, coup franc indirect (sans objet)
- [ ] Suite complète au compte attendu (sans objet : aucun code) ; durée réelle relevée (ci-dessous)

## Constat avant le code (24/11/2026)

- Dans le moteur, le pied ne joue le ballon que jusqu'à la hanche (`atteinte.FOOT_SHARE` = 0,53 × taille), le corps jusqu'à l'épaule (`BODY_SHARE` = 0,82 × taille), la tête au-dessus ; aucun joueur ne lève le pied plus haut (pas de volée haute ni de ciseau) ni ne baisse la tête (pas de tête plongeante).
- Sonde (`.scratch/v2-realisme/mesures/15b3-sonde.py`, matchs 0 et 1 du banc, graines 20260923 et 20260924, chaque appel de `body_part` relevé) : 1 ballon joué au corps sur les 2 matchs ; 2 ballons joués au pied avec un adversaire de champ à 1 m ou moins, aucun à une hauteur au-dessus de la hanche de cet adversaire ; **0** ballon joué au pied ou au corps à hauteur de tête d'un adversaire tout proche. Le jeu dangereux du ticket n'a donc aucune occasion de se produire.
- Le coup franc indirect existe déjà sous forme simplifiée (`match._award_offside_free_kick`, ticket v2-collectif/23) : ce n'est pas lui qui manque, c'est la situation.
- Options présentées au propriétaire : clore sans objet (recommandé), créer un comportement « pied levé » (constantes nouvelles, environ 2 h, effet probablement très rare), reporter. Décision : « Clore sans objet ».
- Durée réelle : environ 20 min (analyse et sonde 15, rédaction 5) sur 1 h 15 estimées, − 73 % : aucun code, le constat suffit. Temps machine hors total : sonde de 2 matchs (environ 2 min 30).

## Comments
