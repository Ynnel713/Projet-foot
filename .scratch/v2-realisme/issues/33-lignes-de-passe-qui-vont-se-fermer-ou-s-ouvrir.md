# 33: Lignes de passe qui vont se fermer ou s'ouvrir : anticiper la réaction adverse

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur l'intelligence de jeu, point 4 « voir les appels et anticiper les réactions adverses »). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (24/11/2026) :** au moment du choix, le risque d'une passe se juge sur la position actuelle des adversaires (perçue, `08d`) par rapport à la ligne de passe (`possession._cut_chance`, table du `18g`) : un défenseur qui court vers la ligne ou qui va sortir sur le porteur ne compte pas plus qu'un défenseur arrêté. À l'exécution, en revanche, les adversaires lisent la passe et courent la couper (`anticipation.pass_readers` : couloir, vitesse de pointe, Anticipation). La décision ne voit donc pas le piège de la ligne qui « semble ouverte » mais va se fermer, ni la ligne qui va s'ouvrir parce qu'un défenseur sort sur le porteur. L'Anticipation du porteur prolonge déjà l'élan des adversaires pour juger l'espace d'une conduite (`decision.anticipation_share`, ticket `v2-collectif/33`), pas pour les passes.

**What to build:** dans l'évaluation des passes, le porteur prolonge l'élan des adversaires qu'il perçoit, avec la même part que pour la conduite (`anticipation_share`, Anticipation, sans courbe nouvelle) : un défenseur lancé vers la ligne la ferme, un défenseur qui sort sur le porteur libère celui qu'il marquait (sa ligne s'ouvre). Le porteur décide sur ce qu'il perçoit et prolonge, jamais sur le futur exact ni sur les tirages à venir (pas de « surhomme omniscient ») ; l'exécution reste physique (`pass_readers`). Lien : troisième homme (`v2-collectif/15b1`, livré), lecture du pressing (`v2-collectif/15b3`), renversement quand un pressing s'emballe d'un côté (`v2-collectif/15d`).

**Ajout du 24/11/2026 (demande du propriétaire du 24/11/2026, éléments sur la technique, point 6 « exploitation par les coéquipiers »).** Cas à couvrir par les scènes : après une élimination par un dribble ou un contrôle orienté (`04g`, `36`), le défenseur suivant sort sur le porteur ; la ligne vers le coéquipier qu'il couvrait s'ouvre, et le porteur qui le prolonge la voit. La mesure en match (passes au joueur libéré après un décalage) est au `39`.

**Attributs :** Anticipation (rôle existant : prolonger l'élan des adversaires, carte) ; Decisions garde l'erreur de perception (existante).

**Blocked by:** rien (dépendances livrées : `v2-collectif/33`, `v2-realisme/08d`). **Bloque :** `v2-realisme/35` (volet de la validation, souple).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne (au-delà de 2 h de peu : découpage examiné au lancement). Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Constantes (horizon de prolongation, s'il en faut un) validées avant le code
- [ ] Scène : défenseur lancé vers une ligne de passe encore ouverte : la passe est moins choisie avec Anticipation 99 qu'avec 11 ; défenseur qui sort sur le porteur : la passe vers celui qu'il marquait est plus choisie
- [ ] Le porteur ne lit que les adversaires perçus (mémoire, vision) : un adversaire non vu ne pèse pas
- [ ] Valeur réelle d'une passe (journal du meilleur choix) : elle prolonge entièrement le déplacement des adversaires réels (part 1, comme `dribble_options(..., 1.0)` pour la conduite) ; seule la valeur perçue utilise `anticipation_share` (réserve A2 de l'expert, 24/11/2026). Test : dans la scène du défenseur lancé vers la ligne, le choix du profil Anticipation 99 est marqué meilleur choix (`best`)
- [ ] Série : passes coupées, pertes, passes réussies, buts encaissés en transition (avant / après) ; indicateurs globaux dans le bruit ou expliqués
- [ ] Rayon des attributs conforme à la carte ; déterminisme ; suite complète au compte attendu ; durée réelle relevée

## Comments
