# 08c: Scan visuel avant la réception

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** perception.

**Constat vérifié :** aucun regard volontaire : le seul geste de « lever la tête » est l'intention textuelle pendant la réception (`cerveau.py:152`).

**What to build:** Un joueur sans ballon peut tourner brièvement la tête (scan) pour mettre à jour sa mémoire hors de son cône ; la fréquence des scans dépend d'un attribut à trancher (recommandation : Vision, qui règle déjà « quelles options il voit » ; Anticipation déjà chargée de la lecture). Un scan coûte un court instant pendant lequel il ne suit plus le ballon.

**Attributs :** Vision (fréquence des scans) ; porteur : Dribbling + Technique cumulés (tête haute) ; parts et constantes proposées au propriétaire avant le code

**Blocked by:** 08b (Mémoire de perception : positions vues, datées et vieillissantes); 07c (Réception de face, de profil ou dos au jeu).

**Bloque :** 08e, `v2-collectif/31`.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Vision règle déjà la portée des passes envisagées (`decision.visible_teammates`) : le scan ne doit pas recompter cette portée.

**Élargi le 13/11/2026 (propriétaire, pendant le 08a).** « Le champ de vision dépend de si le joueur a le ballon ou pas, s'il est arrêté ou en mouvement, un joueur technique a moins besoin de regarder le ballon [...] Un joueur avec un gros QI foot prend l'info plus tôt » ; « ça dépend de la vitesse et de s'il a du monde autour de lui [...] si les adversaires sont plus éloignés il est plus libre et peut mieux prendre l'info ». À intégrer :
- **le porteur aussi** : en conduite, il garde la tête basse une part du temps (il voit peu au-delà du ballon), d'autant moins qu'il est à l'aise balle au pied : **cumul Dribbling + Technique**, parts à proposer (décision du propriétaire : « un peu de dribbling et un peu de technique avec un coeff bien dosé », R2 révisée) ;
- **fréquence des scans** selon Vision (prise d'information, « QI foot »), **la vitesse** (moins de scans à pleine course) et **la gêne** (`possession.pressure` : adversaires proches, moins de temps pour scanner loin) ;
- sources à chercher : fréquences de scan de Jordet (Premier League, avant la réception, selon le poste et la pression), effet de la vitesse ; à défaut, « non trouvé ».
Périmètre plus large que l'estimation de 2 h : à réestimer et à examiner pour découpage avant le code (par exemple sans ballon, puis porteur).

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : fréquences réelles de scan à sourcer.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** après un scan, la mémoire des joueurs dans le dos est à jour
- **Comportementaux (profils comparés) :** Vision 99 contre 11 : plus de scans par minute avant réception

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scans tracés
- [ ] Effet de l'attribut retenu mesuré en scène A/B
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
