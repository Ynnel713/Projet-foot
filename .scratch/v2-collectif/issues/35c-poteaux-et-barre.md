# 35c: Poteaux et barre

**Origine (05/11/2026) :** remarques du propriétaire après le ticket 28a : la façon dont le ballon et le joueur arrivent l'un vers l'autre (ballon fort ou arrêté, de face, de côté ou de dos, joueur lancé ou arrêté, bon ou mauvais pied) change la qualité, la puissance et le dosage d'un tir comme d'une passe. Découpage en petits tickets (environ 2 h chacun, mesure comprise), validé par le propriétaire.

**What to build:** Un tir dont le point d'arrivée touche le cadre (poteau ou barre, rayon du montant plus rayon du ballon) **heurte le montant**. Trois suites, selon l'angle d'arrivée et le côté touché : **rentrant** (but), **renvoyé dans le terrain** (ballon libre, seconds ballons), **sortant** (sortie de but ou corner selon le dernier toucheur). Les poteaux se calculent à plat dès 35b ; la barre demande la hauteur (`v2-hauteur-ballon/02a`). Tracé et rejoué à l'écran.

**Attributs :** Aucun.

**Blocked by:** 35b ; `v2-hauteur-ballon/02a` pour la barre.

**Bloque :** —

**Status:** à faire (constantes à proposer avant le code)

**Hors de ce ticket :** pied fort et pied faible (`v2-attributs-restants/04a`, qui s'applique ensuite à chacun de ces gestes) ; choix du geste (placée, enroulée, `v2-attributs-restants/10a`).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scène contrôlée : un tir visant le poteau à quelques centimètres touche le montant ; selon l'angle, il rentre, revient en jeu ou sort
- [ ] En match : part des tirs sur les montants rapportée (réel à sourcer, de l'ordre de quelques pour cent)
- [ ] La barre ne peut être touchée qu'avec la hauteur du ballon (02a) ; avant, seuls les poteaux
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
