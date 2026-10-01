"""Tests d'import_seed.import_seed -- en particulier la regle "cooldown
obligatoire" (voir README.md et AUDIT_EDITORIAL_2026-09-30.md) : toute phrase
importee doit produire une ligne dans phrase_cooldowns, jamais un
cooldown_matches NULL."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.import_seed import SeedValidationError, _validate_scenarios, import_seed

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "data" / "schema.sql"


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    return db_path


def _write_scenarios_yaml(
    tmp_path: Path, cooldown_matches: int | None, conditions: list[dict[str, Any]] | None = None
) -> Path:
    phrase: dict[str, Any] = {"text": "{joueur} marque !", "weight": 1.0}
    if cooldown_matches is not None:
        phrase["cooldown_matches"] = cooldown_matches
    if conditions is not None:
        phrase["conditions"] = conditions
    scenarios = [
        {
            "code": "BUT",
            "label": "But",
            "variants": [
                {"code": "DEFAUT", "label": "Défaut", "is_default": True, "phrases": [phrase]}
            ],
        }
    ]
    path = tmp_path / "scenarios.yml"
    path.write_text(yaml.safe_dump(scenarios, allow_unicode=True), encoding="utf-8")
    return path


def _write_empty_slots_yaml(tmp_path: Path) -> Path:
    path = tmp_path / "slots.yml"
    path.write_text("{}", encoding="utf-8")
    return path


class TestImportSeedCooldown:
    def test_phrase_with_cooldown_matches_is_inserted_into_phrase_cooldowns(self, tmp_path):
        db_path = _init_db(tmp_path)
        scenarios_path = _write_scenarios_yaml(tmp_path, cooldown_matches=3)
        slots_path = _write_empty_slots_yaml(tmp_path)

        stats = import_seed(db_path, scenarios_path, slots_path)
        assert stats.phrases == 1

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT p.id, pc.cooldown_matches FROM phrases p "
            "JOIN phrase_cooldowns pc ON pc.phrase_id = p.id"
        ).fetchone()
        conn.close()

        assert row is not None
        assert row[1] == 3

    def test_phrase_without_cooldown_matches_fails_the_whole_import(self, tmp_path):
        import pytest

        from scripts.import_seed import SeedValidationError

        db_path = _init_db(tmp_path)
        scenarios_path = _write_scenarios_yaml(tmp_path, cooldown_matches=None)
        slots_path = _write_empty_slots_yaml(tmp_path)

        with pytest.raises(SeedValidationError, match="cooldown_matches"):
            import_seed(db_path, scenarios_path, slots_path)

        # Import refuse "tout ou rien" (voir docstring du module) : aucune
        # ligne ne doit avoir ete ecrite, meme dans scenarios/variants.
        conn = sqlite3.connect(db_path)
        n_scenarios = conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0]
        conn.close()
        assert n_scenarios == 0


class TestImportSeedConditionOperators:
    """Non-regression du bug trouve au 1er import reel des 281 phrases
    (30/09/2026) : le CHECK de phrase_conditions.operator n'incluait pas
    'contient' (56 occurrences dans la banque reelle) ni '=' -- pourtant
    tous deux acceptes par engine.conditions.evaluate_condition. Aucun test
    existant ne le detectait : ceux d'import_seed ne posaient jamais de
    condition, ceux de convert_commentary ne testaient que la validation
    structurelle (_validate_scenarios), jamais une vraie insertion SQLite."""

    def test_contient_operator_is_accepted_by_the_schema(self, tmp_path):
        db_path = _init_db(tmp_path)
        scenarios_path = _write_scenarios_yaml(
            tmp_path,
            cooldown_matches=3,
            conditions=[
                {"attribute": "preferred_moves", "operator": "contient", "value": "Shoots With Power"}
            ],
        )
        slots_path = _write_empty_slots_yaml(tmp_path)

        stats = import_seed(db_path, scenarios_path, slots_path)
        assert stats.phrases == 1

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT operator FROM phrase_conditions").fetchone()
        conn.close()
        assert row[0] == "contient"


class TestImportSeedNomsDAttributs:
    """D16-fine : un nom d'attribut inconnu fait echouer l'import (tout ou rien) ;
    les noms valides (FM26, champ Player, champ de contexte, preferred_moves) passent,
    y compris ceux que certains joueurs n'ont pas (ecartes a l'execution, pas ici)."""

    @staticmethod
    def _importer(tmp_path: Path, attribute: str) -> Path:
        db_path = _init_db(tmp_path)
        scenarios_path = _write_scenarios_yaml(
            tmp_path,
            cooldown_matches=3,
            conditions=[{"attribute": attribute, "operator": ">=", "value": "70"}],
        )
        import_seed(db_path, scenarios_path, _write_empty_slots_yaml(tmp_path))
        return db_path

    def test_une_faute_de_frappe_fait_echouer_l_import_et_suggere_le_bon_nom(self, tmp_path):
        db_path = _init_db(tmp_path)
        scenarios_path = _write_scenarios_yaml(
            tmp_path,
            cooldown_matches=3,
            conditions=[{"attribute": "Aggresion", "operator": ">=", "value": "70"}],
        )
        with pytest.raises(SeedValidationError, match="Aggresion.*Aggression"):
            import_seed(db_path, scenarios_path, _write_empty_slots_yaml(tmp_path))

        conn = sqlite3.connect(db_path)
        assert conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 0
        conn.close()

    @pytest.mark.parametrize("attribute", ["Aggression", "age", "minute", "is_home", "fm_rating"])
    def test_un_nom_valide_est_accepte(self, tmp_path, attribute):
        db_path = self._importer(tmp_path, attribute)
        conn = sqlite3.connect(db_path)
        assert conn.execute("SELECT attribute FROM phrase_conditions").fetchone()[0] == attribute
        conn.close()

    def test_toutes_les_conditions_de_la_banque_v1_sont_reconnues(self):
        banque = yaml.safe_load(
            (SCHEMA_PATH.parent / "seed" / "scenarios.yml").read_text(encoding="utf-8")
        )
        _validate_scenarios(banque, known_slot_keys=set())


class TestImportSeedUniciteDesTextes:
    """Un meme texte deux fois dans une variante : refuse a l'import (avant toute
    ecriture) ET par l'index UNIQUE (ceinture). Le meme texte dans deux variantes
    ou deux scenarios reste autorise."""

    @staticmethod
    def _ecrire(tmp_path: Path, textes_par_variante: dict[str, list[str]]) -> Path:
        variantes = [
            {
                "code": code,
                "label": code,
                "is_default": code == "DEFAUT",
                "phrases": [{"text": t, "weight": 1.0, "cooldown_matches": 3} for t in textes],
            }
            for code, textes in textes_par_variante.items()
        ]
        path = tmp_path / "scenarios.yml"
        path.write_text(
            yaml.safe_dump([{"code": "BUT", "label": "But", "variants": variantes}], allow_unicode=True),
            encoding="utf-8",
        )
        return path

    def test_deux_textes_identiques_dans_une_variante_font_echouer_l_import(self, tmp_path):
        db_path = _init_db(tmp_path)
        scenarios_path = self._ecrire(tmp_path, {"DEFAUT": ["{joueur} marque !", "{joueur} marque !"]})
        with pytest.raises(SeedValidationError, match=r"BUT.*DEFAUT.*en double"):
            import_seed(db_path, scenarios_path, _write_empty_slots_yaml(tmp_path))

        conn = sqlite3.connect(db_path)
        assert conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 0
        conn.close()

    def test_le_meme_texte_dans_deux_variantes_est_autorise(self, tmp_path):
        db_path = _init_db(tmp_path)
        scenarios_path = self._ecrire(
            tmp_path, {"DEFAUT": ["{joueur} marque !"], "SURNOM": ["{joueur} marque !"]}
        )
        stats = import_seed(db_path, scenarios_path, _write_empty_slots_yaml(tmp_path))
        assert stats.phrases == 2

    def test_l_index_unique_refuse_le_doublon_meme_sans_passer_par_import_seed(self, tmp_path):
        db_path = _init_db(tmp_path)
        conn = sqlite3.connect(db_path)
        conn.execute("INSERT INTO scenarios (code, label) VALUES ('BUT', 'But')")
        conn.execute("INSERT INTO variants (scenario_id, code, label, is_default) VALUES (1, 'DEFAUT', 'd', 1)")
        conn.execute("INSERT INTO phrases (variant_id, text) VALUES (1, 'x')")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO phrases (variant_id, text) VALUES (1, 'x')")
        conn.close()


class TestImportSeedListeDeFichiers:
    """D4 : import_seed accepte une liste de YAML de scenarios (un par pilote)."""

    @staticmethod
    def _yaml_pour(tmp_path: Path, nom: str, code_scenario: str) -> Path:
        scenarios = [
            {
                "code": code_scenario,
                "label": code_scenario,
                "variants": [
                    {
                        "code": "DEFAUT",
                        "label": "d",
                        "is_default": True,
                        "phrases": [{"text": f"texte {code_scenario}", "cooldown_matches": 2}],
                    }
                ],
            }
        ]
        path = tmp_path / nom
        path.write_text(yaml.safe_dump(scenarios, allow_unicode=True), encoding="utf-8")
        return path

    def test_une_liste_de_fichiers_est_importee_en_un_seul_import(self, tmp_path):
        db_path = _init_db(tmp_path)
        fichiers = [self._yaml_pour(tmp_path, "a.yml", "BUT"), self._yaml_pour(tmp_path, "b.yml", "CORNER")]
        stats = import_seed(db_path, fichiers, _write_empty_slots_yaml(tmp_path))
        assert (stats.scenarios, stats.phrases) == (2, 2)

    def test_str_et_path_seuls_restent_acceptes(self, tmp_path):
        for i, conversion in enumerate((str, Path)):
            sous_dossier = tmp_path / str(i)
            sous_dossier.mkdir()
            db_path = _init_db(sous_dossier)
            fichier = self._yaml_pour(sous_dossier, "a.yml", "BUT")
            stats = import_seed(db_path, conversion(fichier), _write_empty_slots_yaml(sous_dossier))
            assert stats.scenarios == 1

    def test_un_code_present_dans_deux_fichiers_est_refuse_avant_toute_ecriture(self, tmp_path):
        db_path = _init_db(tmp_path)
        fichiers = [self._yaml_pour(tmp_path, "a.yml", "BUT"), self._yaml_pour(tmp_path, "b.yml", "BUT")]
        with pytest.raises(SeedValidationError, match=r'"BUT".*a\.yml.*b\.yml'):
            import_seed(db_path, fichiers, _write_empty_slots_yaml(tmp_path))

        conn = sqlite3.connect(db_path)
        assert conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 0
        conn.close()

    def test_le_defaut_est_la_banque_v1_puis_les_yaml_du_dossier_v2(self, tmp_path, monkeypatch):
        import scripts.import_seed as module

        (tmp_path / "defense.yml").write_text("[]", encoding="utf-8")
        (tmp_path / "corner.yml").write_text("[]", encoding="utf-8")
        (tmp_path / "notes.md").write_text("pas un yaml", encoding="utf-8")
        monkeypatch.setattr(module, "DEFAULT_V2_DIR", tmp_path)

        assert module._default_scenario_paths() == [
            module.DEFAULT_SCENARIOS_PATH,
            tmp_path / "corner.yml",
            tmp_path / "defense.yml",
        ]

    def test_le_defaut_sans_dossier_v2_est_la_banque_v1_seule(self, tmp_path, monkeypatch):
        import scripts.import_seed as module

        monkeypatch.setattr(module, "DEFAULT_V2_DIR", tmp_path / "absent")
        assert module._default_scenario_paths() == [module.DEFAULT_SCENARIOS_PATH]


class TestImportSeedFallbacks:
    """D10 : un fallback par scenario, ligne de `phrases` a is_fallback=1 sur la variante
    par defaut, ni slot ni condition, ni cooldown ; couverture totale des qu'un fichier existe."""

    @staticmethod
    def _banque(tmp_path: Path, codes: tuple[str, ...] = ("BUT", "CORNER")) -> Path:
        scenarios = [
            {
                "code": code,
                "label": code,
                "variants": [
                    {
                        "code": "DEFAUT",
                        "label": "d",
                        "is_default": True,
                        "phrases": [{"text": f"texte {code}", "cooldown_matches": 2}],
                    },
                    {
                        "code": "SURNOM",
                        "label": "s",
                        "is_default": False,
                        "phrases": [{"text": f"surnom {code}", "cooldown_matches": 2}],
                    },
                ],
            }
            for code in codes
        ]
        path = tmp_path / "scenarios.yml"
        path.write_text(yaml.safe_dump(scenarios, allow_unicode=True), encoding="utf-8")
        return path

    @staticmethod
    def _fallbacks(tmp_path: Path, entrees: list[dict[str, Any]]) -> Path:
        path = tmp_path / "fallback.yml"
        path.write_text(yaml.safe_dump(entrees, allow_unicode=True), encoding="utf-8")
        return path

    def _importer(self, tmp_path: Path, entrees: list[dict[str, Any]]):
        db_path = _init_db(tmp_path)
        stats = import_seed(
            db_path,
            self._banque(tmp_path),
            _write_empty_slots_yaml(tmp_path),
            fallback_path=self._fallbacks(tmp_path, entrees),
        )
        return db_path, stats

    def test_un_fallback_par_scenario_sur_la_variante_par_defaut_et_hors_du_compte_des_phrases(self, tmp_path):
        db_path, stats = self._importer(
            tmp_path,
            [{"scenario": "BUT", "text": "Que de l'action !"}, {"scenario": "CORNER", "text": "Coup de pied de coin."}],
        )
        assert (stats.phrases, stats.fallbacks) == (4, 2)

        conn = sqlite3.connect(db_path)
        try:
            # Test SQL D10 : EXACTEMENT un fallback par scenario (jointure variants), 0 compris.
            par_scenario = conn.execute(
                """SELECT s.code, COUNT(p.id) FROM scenarios s
                   LEFT JOIN variants v ON v.scenario_id = s.id
                   LEFT JOIN phrases p ON p.variant_id = v.id AND p.is_fallback = 1
                   GROUP BY s.code ORDER BY s.code"""
            ).fetchall()
            assert par_scenario == [("BUT", 1), ("CORNER", 1)]

            sur_defaut = conn.execute(
                "SELECT COUNT(*) FROM phrases p JOIN variants v ON v.id = p.variant_id "
                "WHERE p.is_fallback = 1 AND v.is_default = 1"
            ).fetchone()[0]
            assert sur_defaut == 2
            # Jamais soumis au cooldown : les 4 phrases normales en ont un, pas les fallbacks.
            sans_cooldown = conn.execute(
                "SELECT COUNT(*) FROM phrases p LEFT JOIN phrase_cooldowns c ON c.phrase_id = p.id "
                "WHERE c.phrase_id IS NULL"
            ).fetchone()[0]
            assert sans_cooldown == 2
            assert conn.execute("SELECT COUNT(*) FROM phrases WHERE is_fallback = 0").fetchone()[0] == 4
        finally:
            conn.close()

    def test_phrase_is_fallback_est_charge_par_load_phrases(self, tmp_path):
        from engine.scenario_engine import load_phrases

        db_path, _ = self._importer(
            tmp_path, [{"scenario": "BUT", "text": "x"}, {"scenario": "CORNER", "text": "y"}]
        )
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            variante_id = conn.execute(
                "SELECT v.id FROM variants v JOIN scenarios s ON s.id = v.scenario_id "
                "WHERE s.code = 'BUT' AND v.is_default = 1"
            ).fetchone()[0]
            phrases = load_phrases(conn, variante_id)
        finally:
            conn.close()
        assert sorted((p.text, p.is_fallback) for p in phrases) == [("texte BUT", False), ("x", True)]

    @pytest.mark.parametrize(
        ("entrees", "message"),
        [
            ([{"scenario": "BUT", "text": "a"}], r'"CORNER".*0 fallback'),
            (
                [{"scenario": "BUT", "text": "a"}, {"scenario": "BUT", "text": "b"}, {"scenario": "CORNER", "text": "c"}],
                r'"BUT".*2 fallback',
            ),
            ([{"scenario": "BUT", "text": "a"}, {"scenario": "CORNER", "text": "c"}, {"scenario": "VAR", "text": "d"}], r'inconnu "VAR"'),
            ([{"scenario": "BUT", "text": "{joueur} marque"}, {"scenario": "CORNER", "text": "c"}], "slot"),
            ([{"scenario": "BUT", "text": "texte BUT"}, {"scenario": "CORNER", "text": "c"}], "reprend"),
            ([{"scenario": "BUT", "text": "a", "conditions": []}, {"scenario": "CORNER", "text": "c"}], "scenario.*text"),
        ],
        ids=["scenario-sans-fallback", "deux-fallbacks", "scenario-inconnu", "slot", "texte-existant", "cle-inattendue"],
    )
    def test_un_fallback_invalide_refuse_tout_l_import(self, tmp_path, entrees, message):
        db_path = _init_db(tmp_path)
        with pytest.raises(SeedValidationError, match=message):
            import_seed(
                db_path,
                self._banque(tmp_path),
                _write_empty_slots_yaml(tmp_path),
                fallback_path=self._fallbacks(tmp_path, entrees),
            )
        conn = sqlite3.connect(db_path)
        assert conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 0
        conn.close()

    def test_sans_fichier_de_fallback_l_import_reste_possible_avec_un_avertissement(self, tmp_path, caplog):
        db_path = _init_db(tmp_path)
        with caplog.at_level("WARNING"):
            stats = import_seed(
                db_path,
                self._banque(tmp_path),
                _write_empty_slots_yaml(tmp_path),
                fallback_path=[],
            )
        assert (stats.phrases, stats.fallbacks) == (4, 0)
        assert "Aucun fallback" in caplog.text

    def test_l_index_partiel_refuse_deux_fallbacks_sur_la_meme_variante(self, tmp_path):
        db_path, _ = self._importer(
            tmp_path, [{"scenario": "BUT", "text": "x"}, {"scenario": "CORNER", "text": "y"}]
        )
        conn = sqlite3.connect(db_path)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO phrases (variant_id, text, is_fallback) "
                    "SELECT variant_id, 'autre', 1 FROM phrases WHERE text = 'x'"
                )
        finally:
            conn.close()

    def test_le_defaut_lit_le_dossier_fallback(self, tmp_path, monkeypatch):
        import scripts.import_seed as module

        dossier = tmp_path / "fallback"
        dossier.mkdir()
        (dossier / "v1.yml").write_text(
            yaml.safe_dump([{"scenario": "BUT", "text": "x"}, {"scenario": "CORNER", "text": "y"}]),
            encoding="utf-8",
        )
        monkeypatch.setattr(module, "DEFAULT_FALLBACK_DIR", dossier)
        monkeypatch.setattr(module, "DEFAULT_SCENARIOS_PATH", self._banque(tmp_path))
        monkeypatch.setattr(module, "DEFAULT_V2_DIR", tmp_path / "absent")

        db_path = _init_db(tmp_path)
        stats = import_seed(db_path, slots_path=_write_empty_slots_yaml(tmp_path))
        assert stats.fallbacks == 2

    def test_des_scenarios_explicites_n_heritent_pas_des_fallbacks_du_depot(self, tmp_path, monkeypatch):
        import scripts.import_seed as module

        dossier = tmp_path / "fallback"
        dossier.mkdir()
        (dossier / "v1.yml").write_text(yaml.safe_dump([{"scenario": "BUT", "text": "x"}]), encoding="utf-8")
        monkeypatch.setattr(module, "DEFAULT_FALLBACK_DIR", dossier)

        db_path = _init_db(tmp_path)
        stats = import_seed(db_path, self._banque(tmp_path), _write_empty_slots_yaml(tmp_path))
        assert stats.fallbacks == 0
