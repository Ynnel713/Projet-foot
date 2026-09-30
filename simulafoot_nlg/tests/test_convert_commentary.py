import pandas as pd
import pytest
import yaml

from scripts.convert_commentary_xlsx_to_yaml import (
    DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO,
    SLOTS_AUTORISES,
    CommentaryConversionError,
    convertir,
    valider_slots,
)
from scripts.import_seed import SeedValidationError, _validate_scenarios


def _write_xlsx(tmp_path, rows):
    """rows: liste de dicts avec les clés de l'onglet "Phrases" réel."""
    path = tmp_path / "banque.xlsx"
    df = pd.DataFrame(
        rows,
        columns=["scenario_code", "scenario_label", "variant", "phrase", "condition", "weight", "tags"],
    )
    df.to_excel(path, sheet_name="Phrases", index=False)
    return path


def _row(
    scenario="BUT",
    label="But marqué",
    phrase="{joueur} marque !",
    variant=None,
    condition=None,
    weight=None,
    tags=None,
):
    return {
        "scenario_code": scenario,
        "scenario_label": label,
        "variant": variant,
        "phrase": phrase,
        "condition": condition,
        "weight": weight,
        "tags": tags,
    }


class TestValiderSlots:
    def test_allowed_slot_does_not_raise(self):
        valider_slots("{joueur} marque un but superbe !", "BUT", 5)

    def test_disallowed_slot_raises_with_excel_line_number(self):
        with pytest.raises(CommentaryConversionError, match=r"Ligne 42.*\{passeur\}"):
            valider_slots("Il lance {passeur} dans la profondeur.", "BUT", 42)

    def test_slot_valid_in_its_own_scenario(self):
        valider_slots("{passeur} lance {receveur} !", "COUP_FRANC", 7)

    def test_unknown_scenario_raises(self):
        with pytest.raises(CommentaryConversionError, match="SCENARIO_INCONNU"):
            valider_slots("{joueur} marque.", "SCENARIO_INCONNU", 3)

    def test_slots_autorises_matches_the_real_workbook_measurement(self):
        # Verrou contre une régression silencieuse de la table : ces valeurs
        # ont été mesurées sur le vrai classeur du 29/09/2026 (281 phrases),
        # pas devinées -- voir l'échange "commentaire live quali".
        assert SLOTS_AUTORISES["COUP_FRANC"] == frozenset({"adversaire", "passeur", "receveur"})
        assert SLOTS_AUTORISES["PENALTY_RATE"] == frozenset({"adversaire", "joueur"})
        assert "buteur" not in SLOTS_AUTORISES["BUT"]
        assert "gardien" not in SLOTS_AUTORISES["ARRET_GARDIEN"]


class TestConvertir:
    def test_junk_example_row_is_skipped(self, tmp_path):
        xlsx = _write_xlsx(
            tmp_path,
            [
                _row(phrase="↑ Ligne d'exemple en jaune : à remplacer ou supprimer."),
                _row(phrase="{joueur} ajuste le gardien et marque !"),
            ],
        )
        out = tmp_path / "out.yml"

        n = convertir(xlsx, out)

        assert n == 1
        data = yaml.safe_load(out.read_text(encoding="utf-8"))
        all_phrases = [p["text"] for s in data for v in s["variants"] for p in v["phrases"]]
        assert all_phrases == ["{joueur} ajuste le gardien et marque !"]

    def test_row_with_disallowed_slot_fails_the_whole_conversion(self, tmp_path):
        xlsx = _write_xlsx(tmp_path, [_row(scenario="BUT", phrase="{passeur} sert {joueur} qui marque !")])
        out = tmp_path / "out.yml"

        with pytest.raises(CommentaryConversionError, match=r"\{passeur\}"):
            convertir(xlsx, out)

    def test_condition_is_decomposed_into_structured_atoms(self, tmp_path):
        xlsx = _write_xlsx(
            tmp_path,
            [_row(condition='Aggression >= 85 et preferred_moves contient "Dives Into Tackles"')],
        )
        out = tmp_path / "out.yml"

        convertir(xlsx, out)

        data = yaml.safe_load(out.read_text(encoding="utf-8"))
        conditions = data[0]["variants"][0]["phrases"][0]["conditions"]
        assert conditions == [
            {"attribute": "Aggression", "operator": ">=", "value": "85", "mandatory": True},
            {
                "attribute": "preferred_moves",
                "operator": "contient",
                "value": "Dives Into Tackles",
                "mandatory": True,
            },
        ]

    def test_blank_variant_becomes_the_default(self, tmp_path):
        xlsx = _write_xlsx(
            tmp_path,
            [
                _row(phrase="{joueur} marque un but classique !"),
                _row(phrase="Le colosse s'impose de la tête !", variant="SURNOM"),
            ],
        )
        out = tmp_path / "out.yml"

        convertir(xlsx, out)

        data = yaml.safe_load(out.read_text(encoding="utf-8"))
        variants = {v["code"]: v["is_default"] for v in data[0]["variants"]}
        assert variants == {"DEFAUT": True, "SURNOM": False}

    def test_scenario_with_only_a_named_variant_makes_it_the_implicit_default(self, tmp_path):
        # Cas réel : PENALTY_RATE a 15 phrases, TOUTES taguées variante
        # "PENALTY", aucune ligne à variante vide.
        xlsx = _write_xlsx(
            tmp_path,
            [
                _row(
                    scenario="PENALTY_RATE",
                    label="Penalty manqué",
                    phrase="{joueur} manque son penalty !",
                    variant="PENALTY",
                )
            ],
        )
        out = tmp_path / "out.yml"

        convertir(xlsx, out)

        data = yaml.safe_load(out.read_text(encoding="utf-8"))
        assert data[0]["variants"][0]["code"] == "PENALTY"
        assert data[0]["variants"][0]["is_default"] is True

    def test_output_satisfies_import_seed_default_variant_rule(self, tmp_path):
        # Non-régression de bout en bout : le YAML produit doit passer la
        # validation de scripts/import_seed.py sans modification.
        xlsx = _write_xlsx(
            tmp_path,
            [
                _row(scenario="BUT", phrase="{joueur} marque !"),
                _row(
                    scenario="PENALTY_RATE",
                    label="Penalty manqué",
                    phrase="{joueur} manque !",
                    variant="PENALTY",
                ),
            ],
        )
        out = tmp_path / "out.yml"
        convertir(xlsx, out)

        data = yaml.safe_load(out.read_text(encoding="utf-8"))
        _validate_scenarios(data, known_slot_keys=set())  # ne doit pas lever

    def test_known_slots_get_their_template_filler_expression(self, tmp_path):
        xlsx = _write_xlsx(
            tmp_path, [_row(phrase="{joueur} trouve le chemin des filets face à {adversaire} !")]
        )
        out = tmp_path / "out.yml"

        convertir(xlsx, out)

        data = yaml.safe_load(out.read_text(encoding="utf-8"))
        slots = {s["slot_name"]: s["expression"] for s in data[0]["variants"][0]["phrases"][0]["slots"]}
        assert slots == {"joueur": "player.full_name", "adversaire": "context.opponent_team"}

    def test_every_phrase_gets_its_scenario_default_cooldown(self, tmp_path):
        # Aucune colonne "Cooldown" dans l'onglet "Phrases" du classeur reel
        # (voir DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO) -- verrou de
        # non-regression : ce champ ne doit JAMAIS rester absent/None en
        # sortie, sous peine de faire echouer import_seed (regle "cooldown
        # obligatoire"). Un chiffre unique pour tous les scenarios a ete jugé
        # sous-pensé (2e tour d'audit, 30/09/2026) -- verrouille ici que
        # BUT et CARTON_ROUGE reçoivent des valeurs DIFFERENTES.
        xlsx = _write_xlsx(
            tmp_path,
            [
                _row(scenario="BUT", phrase="{joueur} marque !"),
                _row(
                    scenario="CARTON_ROUGE",
                    label="Carton rouge",
                    phrase="{joueur} voit rouge !",
                ),
            ],
        )
        out = tmp_path / "out.yml"

        convertir(xlsx, out)

        data = yaml.safe_load(out.read_text(encoding="utf-8"))
        cooldowns_par_scenario = {
            s["code"]: p["cooldown_matches"] for s in data for v in s["variants"] for p in v["phrases"]
        }
        assert cooldowns_par_scenario == {
            "BUT": DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO["BUT"],
            "CARTON_ROUGE": DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO["CARTON_ROUGE"],
        }
        assert cooldowns_par_scenario["BUT"] != cooldowns_par_scenario["CARTON_ROUGE"]

    def test_all_allowed_scenarios_have_an_arbitrated_cooldown(self):
        # Garde-fou statique : SLOTS_AUTORISES et
        # DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO doivent lister exactement les
        # memes scenarios -- si l'un des deux grandit sans l'autre,
        # convertir() plante sur le premier scenario concerne (voir son
        # garde-fou), mais ce test le detecte statiquement avant meme une
        # conversion, pour tous les scenarios d'un coup.
        assert set(SLOTS_AUTORISES) == set(DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO)


class TestCooldownObligatoire:
    """La regle "cooldown obligatoire" du README doit etre appliquee des la
    validation (avant toute ecriture SQLite) -- voir import_seed._validate_scenarios."""

    def test_missing_cooldown_matches_fails_validation(self):
        scenarios = [
            {
                "code": "BUT",
                "label": "But",
                "variants": [
                    {
                        "code": "DEFAUT",
                        "label": "Défaut",
                        "is_default": True,
                        "phrases": [{"text": "{joueur} marque !", "weight": 1.0}],
                    }
                ],
            }
        ]
        with pytest.raises(SeedValidationError, match="cooldown_matches"):
            _validate_scenarios(scenarios, known_slot_keys=set())

    def test_explicit_cooldown_matches_passes_validation(self):
        scenarios = [
            {
                "code": "BUT",
                "label": "But",
                "variants": [
                    {
                        "code": "DEFAUT",
                        "label": "Défaut",
                        "is_default": True,
                        "phrases": [
                            {"text": "{joueur} marque !", "weight": 1.0, "cooldown_matches": 3}
                        ],
                    }
                ],
            }
        ]
        _validate_scenarios(scenarios, known_slot_keys=set())  # ne doit pas lever
