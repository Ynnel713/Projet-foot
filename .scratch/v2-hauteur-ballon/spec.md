# Chantier : hauteur du ballon et caméra inclinée (2.5D) dans la V2

Étude complète : `docs/ETUDE_HAUTEUR_V2.md` (audit, architecture cible, risques, constantes proposées, tests).
Décisions prises en séance de questions avec le propriétaire le 03/11/2026 ; D-V03 révisée (`docs/TRD_V2.md`).

## Principe

- Le **moteur V2 calcule la hauteur du ballon** (`z`, `vz`, gravité, rebonds repris de la V1) ; l'écran ne fait que la
  dessiner. Le mode de ballon (« sol », « aérien ») est calculé depuis `z`.
- Les **joueurs restent à plat** dans le moteur ; un saut est un événement de la trace, dessiné par l'écran.
- L'**écran V2 passe en caméra fixe inclinée** (environ 25° depuis la verticale), sans perspective, par une seule
  fonction de projection `(x, y, z) → écran`.
- La V1 n'est pas concernée.

## Tickets et ordre

| Ticket | Contenu | Bloqué par | Place dans l'ordre V2 |
|---|---|---|---|
| `01` | Caméra inclinée (écran V2 seul) | `v2-correctifs-ecran/02` | en parallèle, dès que possible |
| `02` | Hauteur du ballon dans le moteur | `01`, `v2-collectif/28`, `v2-collectif/29` | après `v2-attributs-restants/07`, avant `v2-collectif/32` |
| `03` | Interception selon la hauteur | `02` | juste après `02`, avant `v2-collectif/32` |

Tickets existants qui en dépendent ensuite : `v2-collectif/32` (passe lobée), `v2-attributs-restants/01` (duel
aérien, sauts), puis `v2-attributs-restants/11` (centres variés). Tout est livré avant la calibration
`v2-collectif/22`.

## Hors périmètre (réexaminable)

Perspective avec effet de fuite, caméra mobile ou zoom, effet qui fait dévier le ballon, vent, rotation visible du
ballon, variations de taille des joueurs, postures ou animations expressives, physique verticale des joueurs, V1.
