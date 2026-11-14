# 26a: Contrôle imparfait continu, plus de tout ou rien

**Chantier :** `v2-realisme` (demande du propriétaire du 14/11/2026 : contrôles contextuels, une passe trop appuyée rebondit sur le pied ou force le joueur à s'ajuster ; audit `docs/AUDIT_ROADMAP_V2.md`, « passe et contrôle en tout ou rien »). **Priorité :** P1. **Catégorie :** geste technique.

**Constat vérifié (14/11/2026) :** `possession.attempt_control` tire un succès ou un échec (First Touch contre la difficulté : vitesse du ballon par rapport au ballon idéal, pression). Réussi, le ballon est collé au pied ; raté, il repart à `MISS_SPEED_SHARE` de sa vitesse avec une déviation (`missed_control_velocity`). Entre les deux, rien : pas de contrôle un peu long qui oblige à faire un pas, pas de ballon qui rebondit à 2 m. La posture (type de réception 07c, orientation 07a) joue sur la durée (07d), pas sur la qualité du contact.

**What to build:** l'issue du contrôle devient continue, sur le principe de l'écart gaussien du tir (`v2-collectif/35b`) : distance et direction du ballon après le contact tirées autour de l'intention (pied, ou direction orientée du 31b), avec une dispersion qui croît avec la difficulté (vitesse et angle d'arrivée du ballon, hauteur, type de réception, pression) et décroît avec First Touch (Technique pour les ballons difficiles, rayons de la carte). Le joueur va chercher le ballon là où il est (physique de course existante) ; s'il est trop loin ou qu'un adversaire est plus près, le ballon est libre. Le contrôle raté actuel devient la queue de la distribution, pas un cas à part.

**Hors de ce ticket :** passe à une touche (`v2-collectif/36a`), pied faible (`v2-attributs-restants/04a`), amorti de la poitrine ou de la cuisse (après la hauteur des joueurs, hors périmètre de D-V03).

**Attributs :** First Touch, Technique (rayons existants : la carte doit dire lequel règle la dispersion de quel ballon).

**Ticket 24 en cours :** toute courbe d'attribut de ce ticket passe par `success_probability` / `duel_probability`, dont la forme change au 24 ; les constantes de niveau sont proposées après la livraison du 24.

**Blocked by:** 07c, 07d, `v2-collectif/31b` (livrés) ; 04e, 04f (ballon devant le porteur, ballon jouable entre deux touches : à faire, ils posent la notion de ballon à distance du pied que ce ticket réutilise).

**Bloque :** `v2-collectif/36a` (même calcul de l'arrivée du ballon), `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : 04e et 04f livrés avant (ballon à distance non nulle du pied) ; pas de nouvel état du ballon.
Temps machine, non compté : suite complète ; mesure 50 matchs.

## Tests

- **Scènes :** même joueur, ballon à 8 puis 20 m/s : distance moyenne du ballon après contact plus grande à 20 ; First Touch 99 contre 11 à vitesse égale ; dos au jeu contre de face.
- **Statistiques (50 matchs) :** distribution de la distance après contrôle, pertes au contrôle, temps par possession de joueur.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Distance après contrôle continue (pas deux valeurs) et croissante avec la vitesse d'arrivée, décroissante avec First Touch (scènes)
- [ ] Pertes au contrôle par match dans la marge validée par rapport à avant
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
