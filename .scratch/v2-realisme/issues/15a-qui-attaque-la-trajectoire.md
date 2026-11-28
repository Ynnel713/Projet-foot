# 15a: Qui attaque la trajectoire aérienne

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (seuls les joueurs capables d'arriver au point de chute disputent le ballon). **Catégorie :** décision.

**Constat vérifié :** un ballon aérien ne peut être touché qu'à son point de chute (`ball.aerial_left_m`, ticket 29) ; aucune sélection des joueurs qui l'attaquent.

**What to build:** Pour un ballon aérien, chaque équipe désigne au plus deux joueurs qui vont au point de contact (temps d'arrivée et hauteur atteignable, `v2-hauteur-ballon/03`) ; les autres se placent pour le second ballon.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/01` : sélection.

**Blocked by:** `v2-hauteur-ballon/03`.

**Bloque :** 15b, 15e, 16a, 16f (par le `15a2`).

**Constat revu le 27/11/2026** : `ball.aerial_left_m` n'existe plus ; depuis `v2-hauteur-ballon/03a`, un joueur touche le ballon s'il passe sous son plafond (`portee.player_ceiling_m`), sur toute la trajectoire. Sur une passe lobée ou une remise aérienne, `ball.readers` est vidé (`match.py`, lancement aérien) : aucun défenseur n'attaque la trajectoire ; le receveur vise `meeting_point`, calculé avec la loi de freinage au sol alors que le ballon en vol ne subit que la traînée (14a2b) : point trop court.

**Constantes (validées par le propriétaire le 27/11/2026)** :
| Constante | Valeur | Source |
|---|---|---|
| Joueurs retenus par équipe | 2 au plus | ticket |
| Marge d'arrivée | 0 s, critère strict comme `pass_readers` : éligible si le joueur peut être, à sa vitesse de pointe, au point de la trajectoire où le bas du ballon passe sous son plafond, au plus tard quand le ballon y passe | aucune nouvelle |
| Comparaisons flottantes | epsilon technique (1e-6 s) sur l'éligibilité et sur le classement ; à marge égale à epsilon près, départage déterministe par le nom du joueur (jamais `hash()`) | technique, pas une constante produit |
| Gardien | exclu de la sélection ; sorties aériennes renvoyées à `v2-attributs-restants/03a` (Aerial Reach) ; il peut toujours capter au contact (03b) | choix du propriétaire |

**Receveur (formalisé le 27/11/2026, décision du propriétaire, pas de « place morte »)** :
- Équipe qui passe : la sélection retient au plus deux joueurs de champ **éligibles**. Le receveur éligible en fait toujours partie, quelle que soit sa marge (prioritaire), et la seconde place va au coéquipier éligible le mieux classé.
- Receveur non éligible : il ne prend pas de place. Il reste la cible prioritaire de la passe (rôle `RECEVEUR`) et vise quand même le point d'attaque aérien (point de chute à défaut), et la sélection peut retenir jusqu'à deux coéquipiers éligibles. Jusqu'à trois joueurs de l'équipe qui passe vont alors vers le ballon.
- Équipe qui défend : au plus deux joueurs de champ éligibles, classés par marge.

**Découpage (validé par le propriétaire le 27/11/2026)** : estimé 3 h 10, au-delà du seuil de 2 h :
- `15a1` : point d'attaque aérien (trajectoire en vol, premier point atteignable sous son plafond), branché sur le receveur ;
- `15a2` : sélection des deux joueurs par équipe, rôle, trace, série de 50 matchs.
Le placement des joueurs non retenus pour le second ballon est renvoyé au `15e` (même décision) : au 15a, ils gardent leur rôle actuel.

**Status:** découpé le 27/11/2026 en `15a1` et `15a2` ; constantes validées le 27/11/2026

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : hauteur du ballon disponible.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** dégagement long : les deux plus aptes de chaque équipe attaquent le ballon, les autres non

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Sélection tracée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
