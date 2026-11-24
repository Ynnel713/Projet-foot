# 03d: Gardien : portée du plongeon selon la taille et la détente (Agility)

**Créé le 23/11/2026** à la demande du propriétaire (« J'aimerais savoir si la portée prend en compte la détente et la taille du gardien »). **Chantier :** `v2-attributs-restants`. **Catégorie :** exécution (arrêt).

**Constat vérifié (23/11/2026) :** l'arrêt se joue sur une portée latérale (`shooting.keeper_reach_m`, ticket `v2-realisme/05b`) : portée debout `KEEPER_STANDING_REACH_M` (1,0 m ; One on Ones la module en face-à-face, `03b1`), puis, après le temps de réaction (Reflexes, `03b1`), un plongeon à `KEEPER_DIVE_MPS` (6,0 m/s, recalé au `v2-realisme/05l`) plafonné à `KEEPER_DIVE_REACH_M` (2,8 m). Vitesse et portée maximale du plongeon sont les mêmes pour tous les gardiens : ni la taille (colonne « Taille FM (cm) » de la base, `Player.taille_fm`) ni Agility n'y entrent. Taille et Aerial Reach sont prévues au `03a` pour les seules sorties sur centres ; Jumping Reach est réservée au duel aérien (`v2-realisme/15b`). **Point clé (constat du `v2-realisme/05l`, `shooting.py`, commentaire de `KEEPER_DIVE_MPS`) :** sur les tirs du banc, « seule la vitesse du plongeon joue, ni la portée maximale ni la réaction » ; la visée (`AIM_INSIDE_POST_M`, 2,5 m à l'intérieur d'un poteau, soit environ 1,16 m de l'axe) fait passer la plupart des tirs loin du plafond de 2,8 m. Une taille qui ne réglerait que la portée maximale risque donc d'être sans effet visible en match (règle de fond de la carte : pas d'attribut branché sans effet).

**What to build:**
- **Taille** : la portée maximale du plongeon (`KEEPER_DIVE_REACH_M`) suit l'envergure, proche de la taille : un grand gardien couvre plus de largeur au bout de son plongeon. **Avant le code**, mesurer sur les traces de tirs (`ShotEvent.keeper_gap_m`, `keeper_time_s`, comme au `05h`/`05l`) la part des tirs cadrés qui passent entre 2,72 et 2,95 m du gardien avec un temps de vol suffisant pour finir le plongeon ; si elle est négligeable, soumettre au propriétaire : (a) effet de la taille limité aux scènes, assumé et documenté ; (b) taille qui module aussi la portée debout hors face-à-face (ordre d'application explicite avec One on Ones, qui la module en face-à-face) ; (c) report de l'effet de la taille au ticket de la hauteur du tir (lucarne), où il comptera vraiment.
- **Détente** : Agility règle la vitesse du plongeon (`KEEPER_DIVE_MPS`) : un gardien explosif atteint plus vite sa portée, donc arrête plus de tirs rapides ou déviés. La carte des attributs le prévoit déjà (Agility : « gardien qui plonge et se relève vite »). Jumping Reach n'y entre pas (hauteur de saut sur ballon aérien : double comptage avec le duel aérien, règle anti double comptage de la carte).
- Gardien de référence : médianes des 50 gardiens notés de Ligue 1 de la base, **189 cm** (de 181 à 204) et **Agility 65** (de 25 à 85). À la référence, ou sans note, portée et vitesse du plongeon inchangées : les taux d'arrêt calibrés au `05l` sont gardés (cadrés arrêtés environ 58 % dans la surface, 81 % hors surface).
- Lecture : Agility par la façade (`condition.effective_rating`, lecture d'un seul attribut) ; la taille n'existe pas dans le moteur : nouveau champ de `PlayerState` rempli au départ du match depuis `Player.taille_fm`, avec un repli (colonne « Taille (cm) », puis la référence) si elle manque, champ partagé avec `03a` et `v2-realisme/15b` ; le profil du gardien au moment du tir passe par `shooting.keeper_profile` (porté par `ShotFlight.keeper_profile`), comme Reflexes et One on Ones.

**Hors périmètre :** hauteur du tir (le moteur n'en a pas encore : tir au-dessus ou en lucarne tiré au sort, `v2-hauteur-ballon/02a`) ; la portée en hauteur (taille, sans Jumping Reach, réservée au duel aérien) est au `v2-realisme/05f` (décision du 24/11/2026). Sorties sur centres : `03a`.

**Attributs :** Agility ; Taille (colonne de la base).

**Ajout du 24/11/2026 (demande du propriétaire du 24/11/2026, éléments sur le gardien, point 3) : temps au sol après un plongeon.** Aujourd'hui, le gardien qui vient de plonger est aussitôt disponible pour le second ballon (aucun temps au sol dans `match` ni `gardien`). Après un plongeon, il reste au sol un court instant, puis se relève, d'autant plus vite que son Agility est haute (carte : « gardien qui plonge et se relève vite ») : le second ballon devient une vraie occasion, le double arrêt reste possible pour un gardien explosif. Constantes à proposer avant le code (temps au sol, effet d'Agility). La portée en hauteur est au `v2-realisme/05f`. **Périmètre élargi : découpage possible** (portée et vitesse du plongeon / temps au sol).

**Blocked by:** `03b1` (livré).

**Bloque :** `v2-collectif/22a` (tout ce qui change le jeu passe avant la calibration, décision du 22/11/2026) ; `03a` (même lecture de la taille du gardien, à partager).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 20 min |
| Développement | 30 min |
| Tests | 35 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 55** (portée et vitesse du plongeon) ; **2 h 40** avec le temps au sol ajouté le 24/11/2026 : découpage à faire au lancement (portée et vitesse / temps au sol) |

Confiance : moyenne (même chemin que Reflexes et One on Ones au `03b1`). Temps machine, non compté : série réelle de 50 matchs appariés, séries forcées (taille 181 contre 204, Agility 25 contre 85 ; 30 matchs chacune), environ 2 h ; suite complète (environ 16 min).

**Constantes à proposer au propriétaire avant le code** (pistes, ordres de grandeur, aucune valeur réelle sourcée pour l'instant ; à rechercher : portée d'un plongeon selon la taille, vitesse de détente latérale d'un gardien) :
- portée maximale du plongeon : 2,8 m à 189 cm, + 1 cm par cm de taille (envergure environ égale à la taille) : 2,72 m à 181 cm, 2,95 m à 204 cm ;
- vitesse du plongeon : 6,0 m/s à Agility 65, + 0,04 m/s par point, bornée à 4,0-7,0 m/s (4,4 m/s à 25, 6,8 m/s à 85). Point à surveiller : c'est le levier qui a fait passer les cadrés arrêtés de 45 à 58,5 % dans la surface au `05l` ; l'écart entre gardiens extrêmes doit rester borné (plafond de la carte).

## Acceptance criteria

- [ ] Repères réels recherchés ; constantes et critères chiffrés proposés au propriétaire avant le code
- [ ] Gardien sans note ou à la référence (189 cm, Agility 65) : portée et vitesse du plongeon identiques à avant (scènes) ; matchs sans notes : mêmes empreintes
- [ ] Part des tirs cadrés dans la bande 2,72-2,95 m mesurée avant le code ; choix (a), (b) ou (c) pour la taille soumis au propriétaire si elle est négligeable
- [ ] Scènes séparées par attribut : Agility seule, tir dont le temps de vol tombe dans la phase de plongeon (plus arrêté à 85 qu'à 25) ; taille seule, tir vers 2,8-2,9 m du gardien (atteint à 204 cm, pas à 181 cm) ; écart borné (plafond de la carte entre extrêmes)
- [ ] Séries forcées (mêmes graines) : part des tirs cadrés arrêtés plus haute à Agility 85 qu'à 25, avec intervalle ; pour la taille, critère selon le choix retenu (intervalle de confiance ou scènes seules) ; série réelle : part des cadrés arrêtés et buts par match avec intervalle, comparés aux repères du `05l`
- [ ] Temps au sol après un plongeon (ajout du 24/11/2026) : constantes validées avant le code ; scène : après un arrêt repoussé, le gardien ne peut pas intervenir pendant son temps au sol, plus court à Agility 85 qu'à 25 ; série : buts sur second ballon après un arrêt rapportés avant et après
- [ ] Carte des attributs (Agility, Taille) et test de rayon à jour ; aucune lecture de Jumping Reach
- [ ] Durée réelle relevée ; déterminisme ; suite V2 verte ; V1 inchangée

## Comments

- 23/11/2026, revue de la rédaction (clôture `projet/ticket-03d`), passage 1 : expert APPROVED_WITH_RESERVATIONS. A1 (portée maximale presque sans effet en match, constat du `05l`), A2 (champ taille absent du moteur) et A3 (scènes à séparer par attribut, bornes de la vitesse à chiffrer) intégrées au ticket avant clôture.
