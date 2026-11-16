# 11o: Prudence au tacle selon le risque de carton (joueur averti, dernier défenseur)

**Chantier :** `v2-realisme` (demande du propriétaire du 16/11/2026, pendant le ticket 11h). **Priorité :** P2. **Catégorie :** décision.

**Besoin (propriétaire, 16/11/2026) :** un joueur déjà averti doit être plus prudent dans ses tacles, puisqu'il risque le second jaune, donc le rouge. Le dernier défenseur sait qu'un tacle fautif peut lui valoir un rouge (occasion de but manifeste annulée, loi 12). Aujourd'hui la V2 ne donne aucun carton : la gravité de la faute est enregistrée (`duel.foul_severity`), sans jaune ni rouge (ticket `v2-attributs-restants/09a`, à faire). Le joueur ne peut donc pas peser ce risque.

**What to build:** une fois les cartons en place (09a), le taux de tentative de tacle (`duel.tackle_attempt_factor`, ticket 11h) est réduit pour un joueur averti, et pour le dernier défenseur selon le risque de rouge. **Contrainte du propriétaire :** le dernier rempart reste une urgence défensive (11h) : il ne doit pas laisser l'attaquant marcher vers le but. La prudence modère donc son tacle sans l'annuler, par exemple en le rendant moins risqué : moins de tacles par derrière, plus de tacles de face. Le réel pèse aussi la faute « professionnelle », où le défenseur accepte le rouge pour empêcher le but ; depuis 2016, dans la surface, une faute commise en jouant le ballon vaut un jaune, pas un rouge.

**Attributs :** à trancher par le propriétaire (règle R1) : Decisions (discernement, déjà lu par le 11h) ou aucun attribut ; Aggression garde la fréquence de base.

**Constantes à proposer avant le code :** facteur pour un joueur averti, facteur pour le dernier défenseur (selon l'angle, dans ou hors de la surface). Chiffre réel : à chercher (taux de fautes des joueurs avertis contre non avertis, Opta ou CIES) ou « non trouvé ».

**Lien avec l'existant :** complète le 11h (angle, urgence, prudence de surface) ; dépend du 09a (cartons) ; la gravité selon l'action reste au `21b`.

**Blocked by:** `v2-attributs-restants/09a` (cartons et expulsions) ; 11h.

**Bloque :** rien.

**Status:** à faire (bloqué par 09a ; constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : faible (dépend de la forme des cartons au 09a). Hypothèses : le 09a expose les cartons de chaque joueur pendant le match ; un facteur de plus dans `tackle_attempt_factor`.
Temps machine, non compté : série appariée de 50 matchs ; suite complète.

## Acceptance criteria

- [ ] Constantes, choix de l'attribut et chiffres réels validés par le propriétaire avant le code
- [ ] Joueur averti : tacles tentés par minute en baisse mesurée par rapport aux non-avertis, seconds jaunes rapportés
- [ ] Dernier défenseur : tentatives toujours possibles (urgence du 11h conservée), tacles par derrière en baisse ; rouges et buts encaissés rapportés
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite complète comparée à l'attendu de `CLAUDE.md`
