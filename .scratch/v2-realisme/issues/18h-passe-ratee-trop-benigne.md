# 18h: Passe ratée trop bénigne

**Chantier :** `v2-realisme`. **Catégorie :** exécution.

**Origine :** ticket 18g (12/11/2026, 50 matchs, graine d'audit). Une passe imprécise (tirage raté de `possession.pass_aim`) ne dévie que de 10 à 25 % de sa longueur (`_MISS_SHARE`) : le receveur visé la rattrape quand même dans 64 % des cas de 10 à 35 m (77 % sous 10 m), hors coupe. La note de Passing pèse donc peu sur l'issue réelle d'une passe ; depuis le 18g, la chance évaluée le reflète fidèlement (table `_MISS_RECOVERED`), ce qui rend jouables des passes très imprécises.

**What to build :** Revoir la conséquence d'une passe ratée (ampleur et direction de la déviation, dosage) pour que Passing compte dans l'issue comme dans le football réel ; chiffres réels à chercher (part des passes ratées récupérées par le receveur visé). Remesurer ensuite la table `_MISS_RECOVERED` du 18g.

**Hors de ce ticket :** coupe en vol (18g) ; calibration finale des passes (`v2-collectif/22a`).

**Attributs :** Passing (aucun rôle nouveau).

**Blocked by :** 18g.

**Status :** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 30 min |
| Développement | 30 min |
| Tests | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h** |

Confiance : faible (chiffres réels à trouver). Temps machine, hors total : séries de 50 matchs, suite complète.

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Part des passes imprécises reçues par le receveur visé, avant/après, sur 50 matchs ; table `_MISS_RECOVERED` remesurée
- [ ] Effet de Passing sur l'issue réelle d'une passe mesuré (scènes A/B)
- [ ] Suite complète comparée à l'attendu de `CLAUDE.md`

## Comments
