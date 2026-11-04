# 02: Généralisation aux 3 autres types d'incident

**What to build:** étend le mécanisme validé par le POC (ticket 01) aux 3 autres types fixes — échauffourée/provocation, faute du dernier défenseur, 2ᵉ jaune cumulatif.

**Blocked by:** 01 (POC — tacle dangereux).

**Status:** en sommeil (04/11/2026) : animation V1 désactivée depuis `70ca9d1` (drapeau `LIVE_AND_ANIMATION_ENABLED = false`, décision du propriétaire du 24/10/2026, effort porté sur la V2). À reprendre tel quel si l'animation V1 est rallumée.

- [ ] Les 3 autres types sont chacun représentés sur l'échantillon de référence quand un carton rouge éligible correspond à leur contexte
- [ ] Le choix du type reste cohérent avec le contexte réel du carton (ex. un 2ᵉ jaune n'est jamais mis en scène comme un tacle dangereux)
- [ ] Déterminisme bit-à-bit vérifié
- [ ] Résultat sportif strictement identique
- [ ] Aucune régression sur les clips hors carton-rouge-autonome
- [ ] Propriétaire valide visuellement la crédibilité des 4 types sur un échantillon de clips

**Note :** `narrative.py`, `templates.py` sous exception (`CLAUDE.md`) — exception à redemander avant de coder.
