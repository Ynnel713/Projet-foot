# 03n: Gardien : placement fin avant la frappe

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur le gardien, point 1 « placement et gestion de l'angle », et point 5 « placement et sens du jeu »). **Priorité :** P2. **Catégorie :** placement.

**Constat vérifié (24/11/2026) :** le gardien se tient exactement sur la bissectrice de l'angle ballon-poteaux (`gardien.bisector_point`, ticket `03b`), à une profondeur qui dépend de la distance du ballon (`03b`), de la ligne défensive (`03c`), du face-à-face (`03e`) et de son style (Rushing Out, `v2-attributs-restants/03b3a`). Sa place suit le ballon à chaque pas, pas la cible d'une passe en cours ; aucun décalage vers le premier poteau sur un angle fermé ; aucun attribut ne règle la justesse de son placement (il est toujours parfaitement placé, `BISECTOR_TOLERANCE_M` n'est qu'un seuil de mesure) ; ses appuis au moment du tir sont pris tels quels (`03f`).

**What to build:**
- **Angle fermé** : sur un tir depuis un côté, le gardien se décale légèrement vers le premier poteau (ne jamais se faire battre au premier poteau), sans ouvrir grand le second.
- **Passe d'approche** : quand une passe part vers un receveur en position de tirer, le gardien se replace déjà vers la bissectrice du point de réception (anticipation), au lieu de suivre seulement le ballon.
- **Se poser avant la frappe** : quand un tireur arme (porteur à portée de tir, orienté vers le but), le gardien ralentit pour être sur ses appuis au départ du tir ; sinon il garde son élan (`03f`), ce qui l'expose au contre-pied.
- **Justesse selon le gardien (Positioning)** : un gardien bien placé tient la bissectrice et la bonne profondeur ; un gardien moins bon s'en écarte un peu (écart tiré, gardé un instant, jamais absurde), ce qui ouvre un côté ou l'expose au lob (`v2-attributs-restants/10b`). Positioning est dans la liste de transition de la garde de rayon : ce rôle de gardien peut lui donner un contexte du registre (ADR 0002), à décider avec le propriétaire.
- Ce qui reste ailleurs : avancée et lob (`10b`), lecture de la frappe et contre-pied (`03l`), sorties (`03m`, `v2-attributs-restants/03a`), écran (`05k`).

**Constantes à proposer avant le code :** décalage vers le premier poteau selon l'angle ; part d'anticipation sur la passe ; distance et ralentissement pour se poser ; écart de placement selon Positioning (repères 11 / 55 / 99). Chiffres réels cherchés (placement des gardiens sur les tirs : données de suivi publiques) ; « non trouvé » sinon.

**Attributs :** Positioning (gardien, rôle nouveau, à inscrire à la carte) ; Anticipation seulement si un contexte du registre le justifie.

**Blocked by:** `03f` (livré). **Bloque :** rien (le `v2-realisme/32` le mesure).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible (au-delà du seuil de 2 h : découpage probable au lancement, par exemple placement géométrique sans attribut / justesse selon Positioning). Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés avant le code ; découpage examiné
- [ ] Scènes : tir depuis un angle fermé : gardien décalé vers le premier poteau ; passe vers un receveur en position de tir : gardien replacé avant la réception ; tireur qui arme : gardien posé au départ du tir
- [ ] Scène A/B : Positioning 99 s'écarte moins de la bissectrice que 11
- [ ] Rayon des attributs conforme à la carte, test de rayon à jour
- [ ] Série : buts par tir cadré, tirs au premier poteau, contre-pieds rapportés ; indicateurs globaux dans le bruit ou expliqués
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; durée réelle relevée

## Comments
