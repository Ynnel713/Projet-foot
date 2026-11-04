# 03: Interception selon la hauteur

**What to build:** avec la vraie hauteur du ballon (ticket 02), un joueur ne joue le ballon que s'il l'atteint dans une
tranche de hauteur accessible à son corps. Remplace les deux règles fondées sur le mode (ticket `v2-collectif/29` :
intouchable en l'air, touchable au point de chute). Étude : `docs/ETUDE_HAUTEUR_V2.md`, section 5.

1. **Tranches par joueur**, calculées depuis sa taille (`Taille FM (cm)`, repli `Taille (cm)`, puis neutre du poste) :
   - pied : ballon jouable du pied ;
   - corps : contrôle de la poitrine ou de la cuisse ;
   - tête : jusqu'à taille + détente, la détente venant de Jumping Reach (rayon fixé dans `docs/CARTE_ATTRIBUTS_V2.md`,
     sans double comptage avec `v2-attributs-restants/01`) ;
   - mains : gardien dans sa surface, bras levés.
2. **Contact sur le trajet** (`v2engine/match.py`) : le ballon qui passe à portée d'un joueur à une hauteur de sa
   tranche peut être touché ; au-dessus, il passe. La qualité du geste reste aux tickets existants (réception 31, duels
   07, tête au ticket `v2-attributs-restants/01`).
3. Ici, pas de duel ni de saut dessiné : un seul joueur touche le ballon, le premier qui l'atteint, comme aujourd'hui.

**Constantes proposées** : seuils des tranches en fraction de la taille et portée du gardien, à sourcer (« non trouvé »
sinon) et à proposer avant le code.

**Blocked by:** 02a (physique de la hauteur).

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Constantes des tranches proposées, sourcées ou notées « non trouvé », validées avant le code
- [ ] Scène fixe : ballon à 2,5 m au-dessus d'un défenseur de 1,70 m : il passe ; repris par un joueur de 1,90 m à
      détente élevée
- [ ] Scène fixe : le gardien capte dans sa surface un ballon hors de portée des joueurs de champ
- [ ] Scène fixe : un ballon à 0,5 m est jouable du pied par tous
- [ ] Mesure sur 50 matchs avant/après : interceptions, possession, passes réussies, buts ; chaque écart expliqué
- [ ] Déterminisme : mêmes empreintes à graine fixée
- [ ] Suite complète au compte attendu ; V1 inchangée
