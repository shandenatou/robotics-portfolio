"""Tests of the newly created documentation helper, not model training tests."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import shutil
import subprocess
import csv
import re
from decimal import Decimal, ROUND_HALF_UP


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "check_portfolio.py"
SPEC = importlib.util.spec_from_file_location("portfolio_check", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PortfolioChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "projects").mkdir()
        (self.root / "projects" / "example.md").write_text("# Example\n", encoding="utf-8")
        (self.root / "README.md").write_text(
            "# Demo\n\n[Example](projects/example.md)\n", encoding="utf-8"
        )
        self.manifest = {
            "schema_version": 1,
            "release_status": "local-draft",
            "projects": [{"id": "example", "path": "projects/example.md"}],
            **{key: "pending" for key in MODULE.APPROVAL_FIELDS},
        }
        self.save_manifest()

    def save_manifest(self):
        (self.root / "portfolio.json").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )

    def test_valid_draft(self):
        self.assertEqual(MODULE.audit(self.root), [])

    def test_unapproved_release_is_blocked(self):
        self.assertEqual(len(MODULE.audit(self.root, release=True)), 5)

    def test_declared_confirmations(self):
        self.manifest.update({key: "confirmed" for key in MODULE.APPROVAL_FIELDS})
        self.manifest["release_status"] = "ready"
        self.save_manifest()
        self.assertEqual(MODULE.audit(self.root, release=True), [])

    def test_missing_link(self):
        (self.root / "README.md").write_text("[missing](absent.md)", encoding="utf-8")
        self.assertTrue(any("local link" in e for e in MODULE.audit(self.root)))

    def test_link_cannot_escape_root(self):
        (self.root / "README.md").write_text("[outside](../outside.md)", encoding="utf-8")
        self.assertTrue(any("local link" in e for e in MODULE.audit(self.root)))

    def test_private_paths_are_flagged(self):
        (self.root / "README.md").write_text("/mnt/private/run", encoding="utf-8")
        self.assertTrue(any("private detail" in e for e in MODULE.audit(self.root)))

    def test_checkpoint_is_flagged(self):
        (self.root / "model.pt").write_bytes(b"synthetic-test-fixture")
        self.assertTrue(any("artifact type" in e for e in MODULE.audit(self.root)))

    def test_duplicate_ids_are_flagged(self):
        self.manifest["projects"].append(self.manifest["projects"][0])
        self.save_manifest()
        self.assertTrue(any("duplicate" in e for e in MODULE.audit(self.root)))

    def test_symlink_is_flagged(self):
        (self.root / "alias.md").symlink_to(self.root / "README.md")
        self.assertTrue(any("symlink" in e for e in MODULE.audit(self.root)))

    def test_manifest_must_be_object(self):
        (self.root / "portfolio.json").write_text("[]", encoding="utf-8")
        self.assertEqual(MODULE.audit(self.root), ["portfolio.json must contain an object"])

    def test_safe_svg(self):
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><defs><marker id="a"/></defs><path marker-end="url(#a)"/></svg>'
        self.assertEqual(MODULE.audit_svg(svg), [])

    def test_svg_external_and_active_content(self):
        for element in ['<script/>', '<image href="https://example.com/a.png"/>', '<path onload="x()"/>']:
            with self.subTest(element=element):
                self.assertTrue(MODULE.audit_svg('<svg xmlns="http://www.w3.org/2000/svg">' + element + '</svg>'))

    def test_svg_invalid_reference(self):
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><path fill="url(https://example.com/x)"/></svg>'
        self.assertTrue(MODULE.audit_svg(svg))

    def test_invalid_svg_xml(self):
        self.assertTrue(MODULE.audit_svg('<svg>'))

    def test_svg_entity_rejected(self):
        self.assertTrue(MODULE.audit_svg('<!DOCTYPE svg><svg/>'))

    def test_svg_private_detail(self):
        (self.root / "diagram.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>/mnt/private/run</text></svg>', encoding="utf-8")
        self.assertTrue(any("private detail" in e for e in MODULE.audit(self.root)))

    def test_html_local_link(self):
        (self.root / "README.md").write_text('<a href="missing.md">link</a>', encoding="utf-8")
        self.assertTrue(any("local link" in e for e in MODULE.audit(self.root)))

    def test_chinese_anchor(self):
        (self.root / "README.md").write_text('<a href="#研究路线">Go</a>\n\n## 研究路线\n', encoding="utf-8")
        self.assertEqual(MODULE.audit(self.root), [])

    def test_missing_anchor(self):
        (self.root / "README.md").write_text('[Go](#absent)', encoding="utf-8")
        self.assertTrue(any("anchor" in e for e in MODULE.audit(self.root)))

    def test_details_balance(self):
        (self.root / "README.md").write_text('<details><summary>Details</summary>', encoding="utf-8")
        self.assertTrue(any("details" in e for e in MODULE.audit(self.root)))

    def test_html_script_rejected(self):
        (self.root / "README.md").write_text('<script>alert(1)</script>', encoding="utf-8")
        self.assertTrue(any("active HTML" in e for e in MODULE.audit(self.root)))

    def test_repository_results_chart(self):
        self.assertEqual(MODULE.audit_results(SCRIPT.parents[1]), [])

    def test_corrupt_results_rejected(self):
        (self.root / "data").mkdir()
        (self.root / "data/results.json").write_text('{"records":[]}', encoding="utf-8")
        self.assertTrue(MODULE.audit_results(self.root))

    def copy_results_fixture(self):
        source = SCRIPT.parents[1]
        (self.root / "data").mkdir()
        (self.root / "assets/diagrams").mkdir(parents=True)
        for relative in ["data/results.json", "assets/diagrams/paired-results.svg"]:
            (self.root / relative).write_bytes((source / relative).read_bytes())

    def test_wrong_pair_counts_rejected(self):
        self.copy_results_fixture()
        file = self.root / "data/results.json"
        data = json.loads(file.read_text())
        data["records"][-1]["paired"]["baseline_only"] = 14
        file.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(any("paired" in e for e in MODULE.audit_results(self.root)))

    def test_wrong_chart_scale_rejected(self):
        self.copy_results_fixture()
        file = self.root / "assets/diagrams/paired-results.svg"
        file.write_text(file.read_text().replace('width="204"', 'width="214"'), encoding="utf-8")
        self.assertTrue(any("scale" in e for e in MODULE.audit_results(self.root)))

    def test_csv_private_path_rejected(self):
        (self.root / "numbers.csv").write_text("id,path\n1,/mnt/private/run\n")
        self.assertTrue(any("private detail" in e for e in MODULE.audit(self.root)))

    def test_csv_numeric_decimal_not_phone(self):
        (self.root / "numbers.csv").write_text("throughput\n1691.15220393255\n")
        self.assertEqual(MODULE.audit(self.root), [])
        (self.root / "numbers.csv").write_text("contact\n13812345678\n")
        self.assertTrue(any("private detail" in e for e in MODULE.audit(self.root)))

    def test_experiment_export_integrity(self):
        self.assertEqual(MODULE.audit_experiment_exports(SCRIPT.parents[1]), [])

    def test_changed_export_rejected(self):
        shutil.copytree(SCRIPT.parents[1] / "data/experiments", self.root / "data/experiments")
        file = self.root / "data/experiments/gwp-paired.csv"
        file.write_text(file.read_text().replace("True", "False", 1))
        errors = MODULE.audit_experiment_exports(self.root)
        self.assertTrue(any("hash mismatch" in e for e in errors))
        self.assertTrue(any("GWP episode count" in e for e in errors))

    def test_memory_success_not_attributed_to_output_bridge(self):
        data = json.loads((SCRIPT.parents[1] / "data/experiments/memory-runs.json").read_text())
        row = next(r for r in data if r["run_id"] == "tower-v2-output-off")
        self.assertEqual(row["history_output_gate_scale"], 0)
        self.assertEqual(row["successes"], 2)
        self.assertEqual(row["history_visual_layers"], [])

    def test_four_data_figures_are_reproducible(self):
        spec = importlib.util.spec_from_file_location("plots", SCRIPT.parent / "plot_experiment_records.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.FIG = self.root
        module.memory()
        module.lingbot()
        module.fastwam()
        module.gwp()
        for name in ["memory-layout-scores.svg", "lingbot-seed-results.svg", "fastwam-training-records.svg", "gwp-training-records.svg"]:
            self.assertEqual((self.root / name).read_bytes(), (SCRIPT.parents[1] / "assets/diagrams" / name).read_bytes())

    def prepare_gitignore_test(self):
        if not shutil.which("git"):
            self.skipTest("git is required to validate packaging rules")
        shutil.copyfile(SCRIPT.parents[1] / ".gitignore", self.root / ".gitignore")
        subprocess.run(["git", "-c", "init.templateDir=", "init", "-q", str(self.root)],
                       check=True, capture_output=True)

    def is_ignored(self, relative):
        result = subprocess.run(["git", "-c", "core.excludesFile=/dev/null",
                                 "check-ignore", "--no-index", relative],
                                cwd=self.root, capture_output=True)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return result.returncode == 0

    def test_reviewed_data_will_be_included_by_git(self):
        self.prepare_gitignore_test()
        source = SCRIPT.parents[1]
        for file in (source / "data").rglob("*"):
            if file.is_file():
                with self.subTest(file=file.name):
                    self.assertFalse(self.is_ignored(str(file.relative_to(source))))

    def test_unreviewed_data_stays_ignored(self):
        self.prepare_gitignore_test()
        for name in ["data/raw.csv", "data/experiments/unreviewed.csv",
                     "data/experiments/unreviewed.json", "datasets/episode.json",
                     "checkpoints/model.pt", "private/notes.md", ".env"]:
            with self.subTest(file=name):
                self.assertTrue(self.is_ignored(name))

    def test_homepage_results_first_and_project_keeps_demos(self):
        source = SCRIPT.parents[1]
        homepage = (source / "README.md").read_text()
        self.assertIsNone(re.search(r"<(?:img|video)\b|!\[", homepage))
        headings = re.findall(r"^## (.+)$", homepage, re.MULTILINE)
        self.assertEqual(headings, ["GWP：价值引导控制", "FastWAM：Flow-GRPO 后训练", "LingBot：预测进度奖励", "GWP：历史记忆", "实验记录"])
        memory = (source / "projects/long-horizon-memory/README.md").read_text()
        self.assertLess(memory.index("## Results"), memory.index("## Demo"))
        self.assertIn("tower-layout-04.gif", memory)
        self.assertIn("tower-layout-10.gif", memory)
        self.assertNotRegex(homepage, r"(?m)^### ")
        self.assertNotIn("旧 Q", homepage)
        for method in ("双 Q", "ASAR", "Flow-GRPO", "Early-A"):
            self.assertIn(method, homepage)
        for name in ("exp005-progress-rl", "exp010-preference", "exp016-lora"):
            self.assertIn(f"projects/reward-action-alignment/experiments/{name}.md", homepage)

    def test_homepage_deltas_match_experiment_exports(self):
        source = SCRIPT.parents[1]
        homepage = (source / "README.md").read_text()
        with (source / "data/experiments/fastwam-evals.csv").open() as file:
            records = list(csv.DictReader(file))
        for phase in ("random", "clean"):
            pair = {r["eval"]: r for r in records if r["phase"] == phase}
            base, candidate = pair["base"], pair["u40"]
            b, c, total = int(base["successes_est"]), int(candidate["successes_est"]), int(base["episodes"])
            self.assertEqual(total, int(candidate["episodes"]))
            detail = (source / "projects/fastwam-policy-optimization/README.md").read_text()
            self.assertIn(f"{b}/{total}", detail)
            self.assertIn(f"{c}/{total}", detail)
        totals = {run: (sum(int(r["successes_est"]) for r in records if r["eval"] == run),
                        sum(int(r["episodes"]) for r in records if r["eval"] == run)) for run in ("base", "u40")}
        b, c = totals["base"], totals["u40"]
        self.assertIn(f"初始策略 {b[0]}/{b[1]} → 后训练 {c[0]}/{c[1]}", homepage)
        memory = json.loads((source / "data/experiments/memory-runs.json").read_text(), parse_float=Decimal)
        runs = {r["run_id"]: r for r in memory}
        def display_score(value):
            # README uses decimal half-up rounding, not binary-float rounding.
            return f"{value.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP):.4f}"
        for baseline, candidate in [("tower-base", "tower-v2-output-off"),
                                    ("put_bottles_into_dustbin-base", "put_bottles_into_dustbin-early-a")]:
            b, c = runs[baseline], runs[candidate]
            self.assertIn(f"{display_score(b['mean_score'])} → **{display_score(c['mean_score'])}**", homepage)
            self.assertIn(f"| {b['successes']}/16 | **{c['successes']}/16** |", homepage)

    def test_rl_formal_evaluations_cover_omitted_versions(self):
        source = SCRIPT.parents[1]
        runs = json.loads((source / "data/experiments/lingbot-formal-evals.json").read_text())
        self.assertEqual({r["run_id"]: r["successes"] for r in runs},
                         {"exp005": 11, "exp007": 8, "exp010": 6, "exp016": 10})
        for run in runs:
            self.assertEqual(run["episodes"], 16)
            self.assertEqual(sum(w["successes"] for w in run["workers"]), run["successes"])

    def test_rl_training_steps_match_selected_configs(self):
        folder = SCRIPT.parents[1] / "data/experiments"
        configs = json.loads((folder / "lingbot-selected-configs.json").read_text())
        for config in configs:
            with (folder / f"lingbot-{config['run_id']}-training.csv").open() as file:
                history = list(csv.DictReader(file))
            self.assertEqual([int(r["step"]) for r in history], list(range(1, config["num_steps"]+1)))
        lora = next(c for c in configs if c["run_id"] == "exp016")
        self.assertEqual(lora["trainable_parameter_count"], 2686976)
        self.assertEqual(len(lora["lora_target_modules"]), 40)

    def test_rl_case_pages_state_baselines_and_limitations(self):
        root = SCRIPT.parents[1] / "projects/reward-action-alignment/experiments"
        for name in ("exp005-progress-rl", "exp010-preference", "exp016-lora"):
            content = (root / f"{name}.md").read_text()
            self.assertIn("## 实验记录", content)
            self.assertIn("## 失败与后续实验", content)
            self.assertIn("11/16", content)
        self.assertIn("同时改变了参数更新范围和学习率", (root / "exp016-lora.md").read_text())

    def test_rl_training_figures_are_reproducible(self):
        spec = importlib.util.spec_from_file_location("rl_plots", SCRIPT.parent / "plot_experiment_records.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.FIG = self.root
        module.rl_cases()
        for exp in ("exp005", "exp010", "exp016"):
            name = f"lingbot-{exp}-training.svg"
            self.assertEqual((self.root / name).read_bytes(), (SCRIPT.parents[1] / "assets/diagrams" / name).read_bytes())

    def test_gwp_paired_improvements_and_pilot_extension(self):
        root = SCRIPT.parents[1]
        with (root / "data/experiments/gwp-qgate-paired.csv").open() as file:
            records = list(csv.DictReader(file))
        self.assertEqual(len({(r["layout_seed"], r["repeat"]) for r in records}), 32)
        for phase, expected in (("pilot8", (5, 7, 8)), ("extension24", (21, 21, 24))):
            part = [r for r in records if r["phase"] == phase]
            self.assertEqual((sum(r["baseline_success"] == "True" for r in part),
                              sum(r["candidate_success"] == "True" for r in part), len(part)), expected)
        with (root / "data/experiments/gwp-asar-paired.csv").open() as file:
            records = list(csv.DictReader(file))
        self.assertEqual((sum(r["old_q_success"] == "True" for r in records),
                          sum(r["world_value_success"] == "True" for r in records), len(records)), (23, 27, 32))
        self.assertEqual(sum(r["old_q_success"] == "False" and r["world_value_success"] == "True" for r in records), 9)

    def test_gwp_baseline_survey_and_stage_f_are_separate(self):
        folder = SCRIPT.parents[1] / "data/experiments"
        baselines = json.loads((folder / "gwp-baseline-evals.json").read_text())
        self.assertEqual({r["task"]: r["successes"] for r in baselines}, {
            "stack_blocks_three":24, "stack_bowls_three":20, "blocks_ranking_size":18,
            "place_dual_shoes":15, "open_microwave":6})
        self.assertEqual(sum(r["episodes"] for r in baselines), 160)
        lora = json.loads((folder / "gwp-stage-f-evals.json").read_text())
        self.assertEqual([r["successes"] for r in lora], [35, 36])
        for run in baselines+lora:
            self.assertEqual(sum(w["successes"] for w in run["workers"]), run["successes"])
            self.assertEqual(sum(w["episodes"] for w in run["workers"]), run["episodes"])
            self.assertEqual(run["episodes"], run["expected"])

    def test_gwp_value_training_and_reproducible_figure(self):
        root = SCRIPT.parents[1]
        with (root / "data/experiments/gwp-value-training.csv").open() as file:
            rows = list(csv.DictReader(file))
        self.assertEqual([int(r["step"]) for r in rows], list(range(1,1501)))
        with (root / "data/experiments/gwp-value-validation.csv").open() as file:
            rows = list(csv.DictReader(file))
        self.assertEqual([int(r["step"]) for r in rows], [1]+list(range(50,1501,50)))
        data = json.loads((root / "data/experiments/gwp-bowls-experiments.json").read_text())
        self.assertEqual(data["value_selected_metrics"]["selected_step"], 500)
        self.assertEqual(data["value_config"]["train_rows"]+data["value_config"]["validation_rows"], 9770)
        spec = importlib.util.spec_from_file_location("value_plots", SCRIPT.parent / "plot_experiment_records.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        module.FIG = self.root; module.gwp_value()
        self.assertEqual((self.root / "gwp-value-training.svg").read_bytes(),
                         (root / "assets/diagrams/gwp-value-training.svg").read_bytes())

    def test_homepage_gwp_results_and_compact_failure_sections(self):
        root = SCRIPT.parents[1]
        content = (root / "README.md").read_text()
        for phrase in ("26/32 → 28/32", "23/32 → 27/32", "projects/gwp-baselines/README.md"):
            self.assertIn(phrase, content)
        self.assertNotIn("失败原因", content)
        for file in (root / "projects/reward-action-alignment/experiments").glob("*.md"):
            section = file.read_text().split("## 失败与后续实验")[1]
            self.assertLessEqual(len(re.findall(r"^\|", section, re.MULTILINE)), 4)

    def test_mc_q_actual_model_and_training_records(self):
        folder = SCRIPT.parents[1] / "data/experiments"
        config = json.loads((folder / "gwp-mc-q-config.json").read_text())
        self.assertEqual(config["lambda_return"], 1.0)
        self.assertEqual(config["variant"], "no_interactions")
        self.assertFalse(config["language_in_critic"])
        self.assertEqual(config["fusion_dim"], 1408)
        self.assertEqual(config["trainable_parameters"], 32074882)
        self.assertEqual(config["features"], ["current_visual", "predicted_future_visual", "action_chunk", "robot_state"])
        with (folder / "gwp-mc-q-training.csv").open() as file:
            rows = list(csv.DictReader(file))
        self.assertEqual([int(r["step"]) for r in rows], [1]+list(range(20,1001,20)))

    def test_detailed_methods_live_in_project_subdirectories(self):
        root = SCRIPT.parents[1]
        cases = {
            "gwp-rl/experiments/mc-return-q-gate.md": ["Huber(Q1", "lambda-return", "512 + 512", "简要失败分析"],
            "gwp-rl/experiments/world-value-asar.md": ["HL-Gaussian", "median/MAD", "256-bin", "简要失败分析"],
            "gwp-rl/experiments/action-expert-lora.md": ["LoRA", "loss", "失败"],
            "fastwam-policy-optimization/experiments/flow-grpo.md": ["sidecar", "advantage", "fastwam-updates.csv"],
            "long-horizon-memory/experiments/early-action-history.md": ["history_recent_count", "recent_capacity", "训练配置"],
        }
        for path, terms in cases.items():
            with self.subTest(path=path):
                text = (root / "projects" / path).read_text()
                for term in terms:
                    self.assertIn(term, text)
                self.assertRegex(text, r"!\[.+\]\(../../../assets/diagrams/.+-method.svg\)")
                self.assertIn("../../../data/experiments/", text)

    def test_gwp_baselines_and_experiment_intent_are_explicit(self):
        root = SCRIPT.parents[1]
        home = (root / "README.md").read_text().split('<a id="fastwam">')[0]
        for term in ("90K EMA", "50-task SFT", "基线直接执行", "这组基线是 Twin-Q＋ASAR", "独立配对实验"):
            self.assertIn(term, home)
        for case in ("mc-return-q-gate", "world-value-asar", "action-expert-lora"):
            content = (root / f"projects/gwp-rl/experiments/{case}.md").read_text()
            self.assertEqual(re.findall(r"^## (.+)$", content, re.MULTILINE)[0], "实验目的与基线")
            for term in ("90K EMA", "基线", "改进方法"):
                self.assertIn(term, content)
        overview = (root / "projects/gwp-rl/README.md").read_text()
        self.assertIn("20/32", overview)
        self.assertIn("另一套场景协议", overview)
        self.assertIn("不是原始 SFT", overview)

    def test_method_figures_remain_compact(self):
        import xml.etree.ElementTree as ET
        for file in (SCRIPT.parents[1] / "assets/diagrams").glob("*-method.svg"):
            with self.subTest(file=file.name):
                svg = ET.parse(file).getroot()
                self.assertLessEqual(int(svg.attrib["height"]), 650)
                self.assertEqual(int(svg.attrib["width"]), 960)

    def test_method_diagrams_are_reproducible_and_inert(self):
        spec = importlib.util.spec_from_file_location("method_diagrams", SCRIPT.parent / "draw_method_diagrams.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.FIG = self.root
        module.build()
        files = list(self.root.glob("*-method.svg"))
        self.assertEqual(len(files), 7)
        for file in files:
            with self.subTest(diagram=file.name):
                self.assertEqual(file.read_bytes(), (SCRIPT.parents[1] / "assets/diagrams" / file.name).read_bytes())
                self.assertEqual(MODULE.audit_svg(file.read_text()), [])


if __name__ == "__main__":
    unittest.main()
