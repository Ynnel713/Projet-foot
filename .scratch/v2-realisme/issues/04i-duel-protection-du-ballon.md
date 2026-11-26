# 04i: Duel : protection du ballon dos au défenseur

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un attaquant puissant garde le ballon dos au but). **Catégorie :** exécution.

**Constat vérifié :** Strength n'intervient que dans la résistance au tacle (`duel.tackle_success_probability`) ; aucun geste de protection.

**What to build:** Porteur au contact et dos au défenseur (type de réception du 07c ou orientation) : il peut protéger le ballon (rester entre le défenseur et le ballon) ; le défenseur ne peut tacler qu'en contournant ou en faisant faute. Strength règle la tenue du contact.

**Attributs :** Strength (tenue du contact)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/07a` : protection.

**Blocked by:** 04a (Conduite : même risque de perte à l'évaluation et à la résolution); 07c (Réception de face, de profil ou dos au jeu); 11b (Collision asymétrique : Strength) ; volet « dès la réception » du complément du 26/11/2026 : 10l (marqueur collé).

**Bloque :** 21c (ajouté le 10/11/2026, audit de la roadmap) ; 04o, 04p, 04q (ajoutés le 26/11/2026, audit duels et dos au but).

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Strength gagne le contact, Balance joue après (`v2-attributs-restants/07b`, règle R1) : ne pas faire jouer Balance ici.

**Complément de l'audit duels / protection / dos au but (26/11/2026, à valider par le propriétaire) :**
- **Dès la réception** : un receveur dos au jeu, défenseur au contact dans son dos (marqueur collé du `10l`), commence à protéger pendant le contrôle. Strength tient le contact pendant la réception ; contact perdu, le contrôle se dégrade (dispersion du `26a`, ballon échappé du `11n`), sans nouvelle courbe.
- **Micro-ajustements** : pendant la protection, le porteur pivote pour garder son dos face au défenseur qui tente de le contourner (rotation du `07a`, vitesse d'Agility du `07f`, rien de nouveau). Le ballon reste du côté opposé au défenseur. Le défenseur qui fait le tour plus vite que le porteur ne pivote retrouve un angle de tacle (de côté, `11d`).
- **Temporiser** : protéger devient aussi une option du porteur, « garder en attendant » : sa valeur compte le soutien attendu (coéquipier qui arrive, `25c` et `25d`) contre le risque qui monte avec la durée et avec un deuxième adversaire (`04p`). Le choix passe par le `04n` (même monnaie que les autres gestes).
- **Profils attendus en scène** : Strength haute et dos au jeu, ballon gardé nettement plus longtemps ; Strength basse, il lâche plus vite (remise ou perte), sans que la protection soit jamais garantie (garde du `19c`).
- **Périmètre élargi** : l'estimation de 2 h ne couvre plus ces quatre points ; à réestimer et à examiner pour découpage avant le code (par exemple protection au contact, puis réception et temporisation).

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
