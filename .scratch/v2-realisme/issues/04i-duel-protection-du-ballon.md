# 04i: Duel : protection du ballon dos au défenseur

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un attaquant puissant garde le ballon dos au but). **Catégorie :** exécution.

**Constat vérifié :** Strength n'intervient que dans la résistance au tacle (`duel.tackle_success_probability`) ; aucun geste de protection.

**What to build:** Porteur au contact et dos au défenseur (type de réception du 07c ou orientation) : il peut protéger le ballon (rester entre le défenseur et le ballon) ; le défenseur ne peut tacler qu'en contournant ou en faisant faute. Strength règle la tenue du contact.

**Ajout du 24/11/2026 (demande du propriétaire du 24/11/2026, éléments sur la technique, point 1 « prise de balle sous pression, dos au jeu » et point 2 « dribble de conservation »).** Deux cas s'ajoutent à la protection en conduite : (1) **dès la réception** : un receveur pressé dans le dos met le corps entre le presseur et le ballon au premier contact (Strength pour tenir le contact) ; la direction de sa touche relève du seul `36` (pas de second choix de direction ici) ; (2) **conservation de côté** : sous pression sans solution, le porteur garde le ballon dans un petit périmètre (distance du ballon au pied courte, `04e`), en attendant un soutien (`25c`) ou le bon moment (tempo, `34`). Les bras et la hanche restent légaux tant que le contact irrégulier (`21c5`) ne les sanctionne pas.

**Attributs :** Strength (tenue du contact)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/07a` : protection.

**Blocked by:** 04a (Conduite : même risque de perte à l'évaluation et à la résolution); 04e (distance du ballon au pied, volet conservation, ajouté le 24/11/2026); 07c (Réception de face, de profil ou dos au jeu); 11b (Collision asymétrique : Strength).

**Bloque :** 21c (ajouté le 10/11/2026, audit de la roadmap) ; `10m` (ajouté le 24/11/2026).

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Strength gagne le contact, Balance joue après (`v2-attributs-restants/07b`, règle R1) : ne pas faire jouer Balance ici.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : orientation disponible (07a).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** porteur de dos au contact : protection tentée ; de face : jamais
- **Comportementaux (profils comparés) :** Strength 99 contre 11 : protection tenue plus longtemps

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Geste tracé et affiché
- [ ] Effet de Strength mesuré en scène A/B
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
