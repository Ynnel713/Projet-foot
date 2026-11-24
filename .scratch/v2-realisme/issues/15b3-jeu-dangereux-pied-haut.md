# 15b3: Jeu dangereux : pied haut contre une tête

**Chantier :** `v2-realisme` (découpe du `15b`, facultatif, validée par le propriétaire le 24/11/2026). **Priorité :** P3. **Catégorie :** exécution.

**Constat vérifié :** aucun jeu dangereux ; le pied ne joue le ballon que jusqu'à la hanche (`atteinte.FOOT_SHARE`).

**What to build:** un joueur qui joue au pied un ballon à hauteur de tête d'un adversaire tout proche (duel du `15b1`) commet un jeu dangereux : coup franc indirect pour l'adversaire. Constantes à proposer avant le code.

**Blocked by:** `15b1`. **Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

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

- [ ] Constantes validées avant le code
- [ ] Scène : pied haut près d'une tête sifflé, coup franc indirect
- [ ] Suite complète au compte attendu ; durée réelle relevée

## Comments
