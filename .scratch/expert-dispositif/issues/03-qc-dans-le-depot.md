# 03: Contrôle qualité versionné dans le dépôt

**What to build:** Le sous-agent `controle-qualite` et le skill `valider-etape`, appelés à chaque clôture par `/valider-ticket-simulafoot`, n'existaient que dans la configuration globale du poste (`~/.claude/agents/controle-qualite.md`, `~/.claude/skills/valider-etape/SKILL.md`). Sur un autre poste, la clôture d'un ticket était donc impossible. Ils sont copiés à l'identique dans le dépôt (`.claude/agents/controle-qualite.md`, `.claude/skills/valider-etape/SKILL.md`), à la demande du propriétaire (12/11/2026 : « Je souhaite pouvoir avoir les skills également sur l'autre pc notamment l'expert et le QC »). L'expert et `valider-ticket-simulafoot` étaient déjà versionnés.

**Blocked by:** 01.

**Status:** livré (12/11/2026), validé expert + QC

- [x] Copies identiques octet pour octet aux versions globales du 12/11/2026 (`cmp`)
- [x] Aucun chemin propre au poste dans les deux fichiers
- [x] Frontmatter valide (`name` cohérent avec le dossier du skill et le nom du fichier de l'agent)
- [x] Le sous-agent reste en lecture seule (outils Read, Grep, Glob)
- [x] Aucun autre fichier de configuration modifié ; suite de tests non concernée (aucun code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 5 min |
| Développement | 5 min |
| Tests | 0 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **20 min** |

Confiance : élevée. Hypothèse : copie sans modification.

## Comments

**12/11/2026, passage 1.** Expert : APPROVED (rapport réémis une fois : ligne Ticket avec le chemin, refusée par le script, clôture BLOQUÉ journalisée). QC : VALIDÉ. Clôture : VALIDÉ. Remarque facultative A1 de l'expert : le skill se dit « version 0.2 », en retard sur le verrou et le contrôle d'intégrité du dépôt ; à corriger dans les deux exemplaires (global et dépôt) ensemble, si le propriétaire le souhaite. Point à surveiller : deux exemplaires qui peuvent diverger.

