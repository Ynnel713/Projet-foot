# 05c: Décision de remplacer : qui sort, selon la fatigue, le carton, la performance et la consigne

**Chantier :** `v2-coach-et-gestion-de-match` (audit des remplacements du 26/11/2026, demande du propriétaire, ticket proposé « S2 »). **Catégorie :** décision.

**Constat vérifié (26/11/2026) :**
- Aucun remplacement dans `v2engine/` aujourd'hui.
- Prévu : 05a choisit le sortant sur la **fatigue** seule (réserve d'énergie `v2-realisme/12e`) ; 05b choisit l'**entrant** selon le score et le style, et traite l'expulsion et la blessure.
- Manquent, côté sortant :
  - le joueur **averti** qu'on sort pour ne pas finir à dix (rien dans 05b, seulement l'expulsé jamais remplacé ; `v2-realisme/11o` règle sa prudence au tacle, pas sa sortie) ;
  - le joueur **en difficulté** : le moteur n'a aucune mesure de la performance d'un joueur pendant le match (la seule note est la Moyenne FM, fixe, `scripts/v2_resultats.py`) ;
  - la combinaison des raisons : aujourd'hui une seule raison par ticket, sans arbitrage quand le plus fatigué n'est pas le plus menacé.

**What to build:**
1. **Indice de performance du match, vu par le coach.** Par joueur, sur une fenêtre glissante (durée à proposer), à partir de la trace : pertes de balle, passes perdues et contrôles ratés (journal `v2-realisme/19b`), duels perdus (`DUEL_EPAULE`, `other` le perdant ; pertes au tacle, `PERTE` avec son `detail`), fautes (`FAUTE` du journal, `MatchTrace.fouls`, `v2-collectif/30`), rapportés à ce qu'on attend de ses notes à ce poste (attendu mesuré sur une série, jamais la Moyenne FM, D-V07). Lu par la décision seulement : il ne change aucun geste du joueur.
2. **Score de sortie par joueur de champ** (et gardien sur blessure seulement), somme pondérée de quatre termes normalisés :
   - fatigue : réserve d'énergie (`12e`) et lucidité (`v2-realisme/20b` quand il est livré) ;
   - carton : averti, plus fort pour un défenseur et quand il reste beaucoup de temps (`v2-attributs-restants/09a`) ;
   - performance : l'indice du point 1 ;
   - consigne du coach : le besoin de profil selon le score et le style (02, 05b) favorise la sortie du profil opposé.
3. **Décision.** À un arrêt de jeu, le coach remplace si le meilleur score dépasse un seuil qui baisse avec la minute (pas de remplacement de confort avant la mi-temps sauf blessure, 05a), dans la limite des remplacements et fenêtres restants (05a). Le sortant est celui au plus haut score ; l'entrant est choisi par 05b. Raison principale tracée (terme dominant).

**Attributs :** aucun nouveau. Stamina via la fatigue (`12e`) ; attributs seuls pour l'attendu de l'indice de performance (D-V07). Le style du coach passe par la consigne (02), pas par un second calcul (règle commune du chantier, anti double comptage).

**Constantes à proposer avant le code :** fenêtre de l'indice de performance ; poids des quatre termes ; seuil de décision et sa pente selon la minute ; majoration du carton selon le poste et le temps restant. Chiffres réels à sourcer, sinon « non trouvé » : part des joueurs avertis remplacés et minute de leur sortie ; minute du premier remplacement ; part des remplacements à la mi-temps.

**Blocked by:** 05a, 05b, 02 ; `v2-realisme/19b`, `12e` (livrés) ; `v2-attributs-restants/09a` (terme « carton ») et `v2-realisme/20b` (terme « lucidité ») : dépendance partielle, comme au 05b. 05c peut être livré avant eux avec ces termes neutres (poids nul) ; chacun est branché et testé à la livraison de son ticket, qui le liste pour cela dans « Bloque ».

**Hors de ce ticket :** `v2-realisme/30a` (options offensives ignorées) et `25h` (jeu sans ballon), cités dans la demande comme sources de performance : ce sont un diagnostic et une validation du collectif, ils ne mesurent pas la performance d'un joueur pendant le match ; l'indice du point 1 la mesure.

**Bloque :** 05d.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (indice, score, décision) | 55 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : faible. Hypothèses : 05a et 05b livrés (banc, fenêtres, choix de l'entrant) ; journal 19b assez riche pour l'indice sans nouvel événement ; attendu de l'indice mesuré sur une série existante. Découpage examiné (26/11/2026) : non retenu. L'indice seul ne livre rien d'observable sans la décision qui le lit, et le dépassement du seuil indicatif est de 10 min ; à réexaminer si l'estimation monte au lancement.
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs ; série pour l'attendu de l'indice.

## Tests

- **Scènes :** à fatigue égale, l'averti sort avant le non-averti ; à carton égal, le plus fatigué sort ; un joueur à l'indice de performance très bas sort avant un joueur moyen de même fatigue ; équipe menée, consigne offensive : un défensif sort avant un offensif de même score ; jamais de remplacement quand plus de fenêtre ou de remplacement disponible.
- **Statistiques (50 matchs) :** raisons des remplacements (part de chacune), minute des remplacements, avertis remplacés, sortants comparés aux restants au même poste (fatigue, indice).

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Chaque terme agit seul à scène égale, dans le sens attendu (scènes), jamais de façon binaire
- [ ] L'indice de performance ne modifie aucun geste ni aucune note du joueur (test) ; attendu tiré des attributs, jamais de la Moyenne FM
- [ ] En match : raison principale tracée pour chaque remplacement ; part des raisons et minute rapportées et comparées aux chiffres réels, sans réglage générique
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
