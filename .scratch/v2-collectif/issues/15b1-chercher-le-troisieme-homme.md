# 15b1: Chercher le troisième homme en construction (contexte « lecture du pressing »)

**Découpé du ticket 15b le 17/11/2026** (décision du propriétaire : « je valide »). **Chantier :** `v2-collectif`. **Priorité :** P1. **Catégorie :** décision.

**Constat avant le code (17/11/2026, 12 matchs de 90 min, script hors dépôt `constat.py`) :** le troisième homme existe déjà par la suite du receveur (ticket 13), le plan de passe (14) et le jeu de première (31a), sans être cherché. Par match : 93,3 passes de construction (gardien ou défenseur dans ses 35 m), dont 6,2 relances longues ; 31,1 % des passes courtes cassent directement la première ligne ; **troisième homme** (A → B → C, B devant la première ligne, C derrière, B rejoue en moins de 4 s, C contrôle) **8,3 par match, 9,6 % des passes courtes**, B en une touche dans 39 % des cas ; pertes dans son propre tiers 12,3 par match (4,9 % des changements de possession). Première ligne : le plus reculé des 3 adversaires de champ les plus avancés (approximation de mesure).

**What to build:** en construction (`bloc.builds_up`) sous pressing, le porteur lit la structure du pressing : il repère un coéquipier C libre derrière la première ligne, accessible par la remise d'un B situé devant. Cette lecture passe par un nouveau contexte du registre, « lecture du pressing » (perception) ; quand il la fait (tirage, flux décision), la suite du receveur vers ce C (`_pass_option`, valeur future du ticket 13) est majorée. Le plan de passe (14) transmet ensuite C à B, qui l'adopte selon son Teamwork (inchangé, pas de nouvelle lecture).

**Hors de ce ticket :** attirer le pressing (15b2) ; court ou long (15a) ; nouveau mécanisme de passe.

**Attributs (ADR 0002) :** contexte « lecture du pressing », perception, Vision 0,5 + Anticipation 0,3 + Decisions 0,2 (proposés, à valider), effet `decision.reads_third_man_probability`. Vision garde la portée des passes envisagées (`visible_teammates`, autre effet) ; Decisions garde l'erreur de perception de toutes les options (`perception_error`, autre effet) ; Teamwork reste dans l'adoption du plan (14), non relu ; Passing dans l'exécution. Un effet, un calcul.

**Blocked by:** `v2-attributs-contextes/02` et `02b` (livrés).

**Status:** à faire (constantes à valider avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min (constat déjà fait) |
| Développement | 40 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : la suite du receveur (13) et le plan (14) portent le troisième homme, il suffit de majorer la suite lue ; un seul calage après la première série.
Temps machine, non compté : séries de 50 matchs avant et après ; suite complète.

## Acceptance criteria

- [ ] Constantes produit validées par le propriétaire avant le code (chiffres réels sourcés ou « non trouvé »)
- [ ] Contexte « lecture du pressing » dans le registre et dans la section « Contextes » de la carte ; Vision, Anticipation et Decisions mis à jour dans la liste de transition (garde de rayon verte)
- [ ] Scène : sous pressing, avec un C libre derrière la première ligne et un B devant, le porteur à lecture 99 sert B plus souvent qu'à 11 ; sans pressing ou hors construction, aucun changement
- [ ] Statistiques (50 matchs, avant et après) : part de troisièmes hommes dans les passes courtes de construction, pertes dans son propre tiers, buts et tirs (calibration)
- [ ] Effet probabiliste, jamais binaire ; plafond d'écart 99 / 11 (`scripts/measure_v2.py --profil`)
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs (ticket 22)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite complète passée, compte comparé à l'attendu de `CLAUDE.md` ; durée réelle relevée

## Sources

- Repère réel du troisième homme en construction : **non trouvé**. Plus proches : Footballytics (Bundesliga 2023-24), attaques par troisième homme réussies et finies dans le dernier tiers, 1 à 2 par match pour les meilleures équipes, définition étroite (hors milieu et construction) : https://www.footballytics.ch/post/tactics-and-data-outplay-opponents-with-pass-combinations ; passes qui cassent une ligne, environ 117 par match sur 64 matchs (arXiv 2506.06666) : https://arxiv.org/html/2506.06666v1
