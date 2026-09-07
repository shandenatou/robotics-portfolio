"""Extract reviewed numeric fields from a private archive; never access a server.

This is a documentation tool written in September 2026, not training code.
Usage: python3 tools/import_experiment_records.py --sources PRIVATE_ARCHIVE
Only allowlisted fields are exported. Original paths, prompts, account links,
videos and model files remain outside this repository.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import math
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]


def clean_tuple(value):
    if isinstance(value, list):
        return [clean_tuple(v) for v in value if v != "__tuple__"]
    if isinstance(value, dict):
        return {k: clean_tuple(v) for k, v in value.items()}
    return value


def select(record, fields):
    return {key: record[key] for key in fields if key in record}


def build(sources, root=ROOT):
    dest = root / "data/experiments"
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "retrieved_on": "2026-09-07", "experiments_rerun": False,
                "origin": "allowlisted-fields-extracted-from-existing-server-artifacts",
                "sources": {}, "exports": {}}

    def source(name):
        file = sources / name
        raw = file.read_bytes()
        sid = file.stem
        digest = hashlib.sha256(raw).hexdigest()
        if sid in manifest["sources"]:
            assert manifest["sources"][sid]["sha256"] == digest
        manifest["sources"][sid] = {"filename": file.name, "sha256": digest,
                                     "bytes": len(raw), "location": "private-review-archive"}
        return file, sid

    def read(name):
        file, sid = source(name)
        return json.loads(file.read_text()), sid

    def write(name, value, source_ids, rows=None):
        file = dest / name
        if file.suffix == ".csv":
            assert value
            with file.open("w", newline="", encoding="utf-8") as out:
                writer = csv.DictWriter(out, fieldnames=list(value[0]))
                writer.writeheader()
                writer.writerows(value)
            rows = len(value)
        else:
            file.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        manifest["exports"][name] = {"source_ids": sorted(set(source_ids)), "rows": rows,
                                      "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}

    # FastWAM: keep successes_est as-is; it is not an audited episode count.
    for original, output in [("combined_update_metrics_0_40.csv", "fastwam-updates.csv"),
                             ("combined_rollout_metrics_0_40.csv", "fastwam-rollouts.csv"),
                             ("eval_success_rates.csv", "fastwam-evals.csv")]:
        file, sid = source("old/" + original)
        rows = list(csv.DictReader(file.open()))
        rows = [{k: v for k, v in row.items() if k != "aggregate_path"} for row in rows]
        write(output, rows, [sid])

    # Gallery rows are a secondary review artifact, not simulator raw logs.
    gallery, gid = read("old/data.json")
    episode_fields = ["id", "source", "seed", "episodeIndex", "success", "abortReason",
                      "numSteps", "meanAbsCorrection", "maxAbsCorrection"]
    episodes = [select(e, episode_fields) for e in gallery["episodes"]]
    assert len({e["id"] for e in episodes}) == len(episodes)
    write("lingbot-episodes.csv", episodes, [gid])
    runs = []
    for stat in gallery["sourceStats"]:
        rows = [e for e in episodes if e["source"] == stat["source"]]
        success = sum(e["success"] for e in rows)
        assert len(rows) == stat["episodes"] and success == stat["successes"]
        runs.append({"run_id": stat["source"], "episodes": len(rows), "successes": success,
                     "aborts": sum(bool(e["abortReason"]) for e in rows),
                     "method_in_gallery": stat.get("method", ""), "source_id": gid})
    write("lingbot-runs.csv", runs, [gid])
    dynamics, aid = read("old/action_dynamics_sft_exp005.json")
    fields = ["id", "source", "seed", "success", "abort_reason", "elapsed_sec", "take_action_count",
              "planned_command_count", "planning_failures_total", "num_replans", "position_path_length",
              "mean_position_step", "mean_acceleration", "mean_jerk", "direction_reversal_ratio",
              "stall_ratio_1mm", "mean_replan_boundary_jump", "boundary_to_within_ratio"]
    write("lingbot-action-audit.csv", [select(e, fields) for e in dynamics["episodes"]], [aid])
    ruler, rid = read("old/ruler-summary.json")
    write("lingbot-ruler-eval.json", {**select(ruler, ["task", "succ_num", "completed_total_num",
          "total_num", "missing_or_timeout_num", "succ_rate"]),
          "workers": [select(w, ["succ_num", "total_num", "succ_rate"]) for w in ruler["workers"]]}, [rid], 4)

    # Selected RL case studies: original simulator aggregates, not gallery labels.
    formal, formal_sources = [], []
    for exp in ("exp005", "exp007", "exp010", "exp016"):
        original, sid = read(f"old/lingbot-{exp}-summary.json")
        workers = []
        for item in original["items"]:
            match = re.search(r"worker_(\d+)/stseed-(\d+)/", item["path"])
            assert match, "unknown worker/seed layout"
            workers.append({"worker_id": int(match[1]), "seed_start": int(match[2]),
                            "successes": int(item["succ_num"]), "episodes": int(item["total_num"])})
        record = {"run_id": exp, "source_id": sid, "task": original["task_name"],
                  "successes": int(original["succ_num"]), "episodes": int(original["total_num"]),
                  "completed": int(original["completed_total_num"]), "expected": int(original["expected_total_num"]),
                  "success_rate": original["succ_rate"], "workers": workers}
        assert sum(w["successes"] for w in workers) == record["successes"]
        assert sum(w["episodes"] for w in workers) == record["episodes"] == record["completed"] == record["expected"] == 16
        formal.append(record)
        formal_sources.append(sid)
    write("lingbot-formal-evals.json", formal, formal_sources, len(formal))

    config_fields = ["method", "uses_full_denoise_loop", "uses_single_step_x0", "uses_demo_future_mse",
        "scored_latent", "num_sampling_steps", "guidance_scale", "beta", "lambda_kl", "lambda_disagree",
        "num_steps", "learning_rate", "micro_batch_size", "gradient_accumulation_steps",
        "lora_rank", "lora_alpha", "lora_dropout", "lora_last_n_blocks", "lora_target_modules",
        "trainable_parameter_count", "total_parameter_count", "candidate_group_size", "candidate_depth",
        "evaluator_gradient_enabled", "winner_rule", "preference_objective", "winner_preserving_mu",
        "winner_safeguard", "video_sampling_steps", "action_sampling_steps", "video_guidance_scale",
        "action_guidance_scale", "dpo_beta", "joint_error", "max_consecutive_nonfinite_skips"]
    configs, config_sources = [], []
    for exp in ("exp005", "exp010", "exp016"):
        original, sid = read(f"old/lingbot-{exp}-config.json")
        configs.append({"run_id": exp, "source_id": sid, **select(original, config_fields)})
        config_sources.append(sid)
        file, tid = source(f"old/lingbot-{exp}-train.jsonl")
        history = [json.loads(line) for line in file.read_text().splitlines() if line.strip()]
        assert all(isinstance(v, (int, float)) and math.isfinite(v) for row in history for v in row.values())
        assert len({row["step"] for row in history}) == len(history)
        assert history[-1]["step"] == original["num_steps"]
        write(f"lingbot-{exp}-training.csv", history, [tid])
    write("lingbot-selected-configs.json", configs, config_sources, len(configs))
    source("old/lingbot-experiments.md")
    for report in ("gwp-stage-f-action-lora.md", "gwp-sac-flow-memory.md",
                   "gwp-full-loop-memory.md", "gwp-entropy-loop-memory.md",
                   "gwp-bowls-report.md", "gwp-sft50task-recipe.md"):
        source("wam/" + report)

    # GWP: keep the two paired experiments and the baseline survey distinct.
    pilot, pilot_id = read("wam/gwp-qgate-pilot.json")
    extension, extension_id = read("wam/gwp-qgate-results.json")
    qgate_rows = []
    for phase, data, sid in (("pilot8", pilot, pilot_id), ("extension24", extension, extension_id)):
        for row in data["paired"]:
            qgate_rows.append({"phase": phase, "source_id": sid, "layout_seed": row["layout_seed"],
                "repeat": row.get("repeat", 0), "baseline_success": row["baseline"],
                "candidate_success": row["q_gate"], "baseline_abort": row["baseline_abort"],
                "candidate_abort": row["q_gate_abort"]})
    assert len(qgate_rows) == len({(r["layout_seed"], r["repeat"]) for r in qgate_rows}) == 32
    assert sum(r["baseline_success"] for r in qgate_rows) == 26
    assert sum(r["candidate_success"] for r in qgate_rows) == 28
    write("gwp-qgate-paired.csv", qgate_rows, [pilot_id, extension_id])
    asar, asar_id = read("wam/gwp-asar-results.json")
    asar_rows = [select(row, ["worker_id", "pair_index", "scene_seed", "old_q_success", "world_value_success"])
                 for row in asar["paired"]["items"]]
    assert len(asar_rows) == len({(r["scene_seed"], r["pair_index"]) for r in asar_rows}) == 32
    assert sum(r["old_q_success"] for r in asar_rows) == 23
    assert sum(r["world_value_success"] for r in asar_rows) == 27
    write("gwp-asar-paired.csv", asar_rows, [asar_id])
    value_config, value_config_id = read("wam/gwp-value-config.json")
    value_final, value_final_id = read("wam/gwp-value-final.json")
    config_safe = select(value_config, ["steps", "batch_size", "eval_batch_size", "cache_batch_size", "max_rows",
        "history_length", "num_bins", "failure_penalty", "world_weight", "consistency_weight", "delta_weight",
        "lr", "weight_decay", "validate_interval", "log_interval", "seed", "rows", "train_rows", "validation_rows",
        "t_max", "failure_penalty_chunks", "method", "backbone_frozen", "target"])
    final_safe = {k: v for k, v in value_final.items() if isinstance(v, (float, int)) or k == "status"}
    write("gwp-bowls-experiments.json", {
        "qgate": {"combined": extension["combined_with_previous_heldout_8"],
                  "extension24": {key: select(extension[key], ["episodes", "successes", "aborts", "selections", "overrides", "override_rate"])
                                  for key in ("baseline", "q_gate")}},
        "asar": {"methods": asar["methods"], "paired": select(asar["paired"],
                 ["completed_pairs", "world_value_wins", "old_q_wins", "ties", "exact_two_sided_p"])},
        "value_config": config_safe, "value_selected_metrics": final_safe},
        [pilot_id, extension_id, asar_id, value_config_id, value_final_id])
    file, value_train_id = source("wam/gwp-value-train.jsonl")
    history = [json.loads(line) for line in file.read_text().splitlines() if line.strip()]
    train = [{k: v for k, v in row.items() if k == "step" or k.startswith("train/")} for row in history]
    validation = [{k: v for k, v in row.items() if k == "step" or k.startswith("val/")}
                  for row in history if "val/mae" in row]
    assert [r["step"] for r in train] == list(range(1, 1501))
    assert all(isinstance(v, (float, int)) and math.isfinite(v) for r in train+validation for v in r.values())
    write("gwp-value-training.csv", train, [value_train_id])
    write("gwp-value-validation.csv", validation, [value_train_id])

    # The deployed Q uses MC returns, and its no_interactions variant omits language.
    qfinal, qfinal_id = read("wam/gwp-qgate-final.json")
    qcode_sources = []
    for name in ("gwp-qgate-training-code.py", "gwp-qgate-model.py", "gwp-qgate-experiment.py",
                 "gwp-qgate-launch.sh", "gwp-qgate-training-launch.sh", "gwp-asar-launch.sh"):
        _, sid = source("wam/" + name)
        qcode_sources.append(sid)
    qconfig = {"method": "monte-carlo-return-twin-q-with-conservative-gate",
        "variant": qfinal["variant"], "lambda_return": qfinal["lambda_return"],
        "features": ["current_visual", "predicted_future_visual", "action_chunk", "robot_state"],
        "language_in_critic": False, "gamma": 0.99, "learning_rate": 5e-5, "batch_size": 64,
        "optimizer": "AdamW", "weight_decay": 1e-4, "grad_clip": 1.0,
        "training_steps": qfinal["step"], "seed": 20260804, "validation_interval": 20,
        "fusion_dim": qfinal["fusion_dim"], "trainable_parameters": qfinal["parameter_count"],
        "qgate_candidate_count": 4, "asar_candidate_count": 16, "sampling_steps": 10,
        "execute_steps": 12, "gate_min_improvement": 0.001, "gate_max_disagreement": 0.08,
        "final_metrics": {k: v for k, v in qfinal.items() if k.startswith(("train/", "val/"))}}
    assert qfinal["variant"] == "no_interactions" and qfinal["lambda_return"] == 1.0
    write("gwp-mc-q-config.json", qconfig, [qfinal_id]+qcode_sources)
    file, qtrain_id = source("wam/gwp-qgate-train.jsonl")
    qhistory = [json.loads(line) for line in file.read_text().splitlines() if line.strip()]
    qnumeric = [{k: v for k, v in row.items() if isinstance(v, (int, float))} for row in qhistory]
    assert [r["step"] for r in qnumeric] == [1]+list(range(20,1001,20))
    assert all(math.isfinite(v) for r in qnumeric for v in r.values())
    write("gwp-mc-q-training.csv", qnumeric, [qtrain_id])

    def gwp_aggregate(filename, run_id, task):
        data, sid = read("wam/" + filename)
        workers = []
        for row in data["items"]:
            match = re.search(r"worker_(\d+)/stseed-(\d+)/", row["path"])
            assert match
            workers.append({"worker_id": int(match[1]), "seed_start": int(match[2]),
                            "successes": int(row["succ_num"]), "episodes": int(row["total_num"])})
        result = {"run_id": run_id, "task": task, "source_id": sid,
                  "successes": int(data["succ_num"]), "episodes": int(data["total_num"]),
                  "expected": int(data["expected_total_num"]), "client_failures": data["client_failures"],
                  "success_rate": data["succ_rate"], "workers": workers}
        assert sum(w["successes"] for w in workers) == result["successes"]
        assert sum(w["episodes"] for w in workers) == result["episodes"] == result["expected"]
        return result

    baselines = [gwp_aggregate(f"gwp-baseline-{task}.json", "sft90k-randomized", task)
                 for task in ("stack_blocks_three", "stack_bowls_three", "blocks_ranking_size", "place_dual_shoes", "open_microwave")]
    write("gwp-baseline-evals.json", baselines, [r["source_id"] for r in baselines], len(baselines))
    lora_evals = [gwp_aggregate(filename, name, "place_dual_shoes") for filename, name in
                  (("gwp-stage-f-base.json", "sft-control"), ("gwp-stage-f-summary.json", "stage-f-lora"))]
    write("gwp-stage-f-evals.json", lora_evals, [r["source_id"] for r in lora_evals], len(lora_evals))

    paired, pid = read("wam/gwp-paired.json")
    rows = [select(e, ["seed", "baseline_success", "candidate_success", "baseline_abort_reason",
                       "candidate_abort_reason"]) for e in paired["paired_episodes"]]
    assert len({r["seed"] for r in rows}) == 64
    assert sum(r["baseline_success"] for r in rows) == paired["baseline_successes"] == 34
    assert sum(r["candidate_success"] for r in rows) == paired["candidate_successes"] == 35
    write("gwp-paired.csv", rows, [pid])
    file, tid = source("wam/gwp-train.jsonl")
    records = [json.loads(line) for line in file.read_text().splitlines() if line.strip()]
    # These metric logs contain numeric scalars only. Reject any unexpected text.
    assert all(isinstance(v, (float, int)) for row in records for v in row.values())
    write("gwp-training.csv", records, [tid])
    selected, sid = read("wam/gwp-selected.json")
    test, testid = read("wam/gwp-test5000.json")
    metric_fields = ["checkpoint_step", "split", "transitions", "episodes", "auroc", "auprc",
                     "brier", "ece", "q1_q2_abs", "preview_only_auroc", "residual_abs_mean",
                     "future_shuffle_auroc", "future_removed_auroc", "action_shuffle_auroc",
                     "same_stage_pairwise_min"]
    metrics = [select(e["validation"], metric_fields) for e in sorted(selected["eligible"], key=lambda e: e["step"])]
    metrics.append(select(test, metric_fields))
    write("gwp-checkpoints.csv", metrics, [sid, testid])
    gate, gateid = read("wam/gwp-gate.json")
    gate_summary = select(gate["summary"], ["thresholds", "target_count", "accepted_group_count",
        "useful_group_count", "pair_count", "rejected_audit_count", "missing_count", "success_count",
        "candidate_count", "split_seed", "split_group_counts", "split_pair_counts"])
    write("gwp-branch-gate.json", {**select(gate, ["deterministic_replay_pass", "all_results_present",
          "has_real_candidate_preferences"]), "summary": gate_summary}, [gateid])

    # Preserve run identity. Reused build_tower baseline is exported once.
    memory_runs, memory_episodes, config_exports, memory_sources = [], [], {}, set()

    def config(name):
        if name in config_exports:
            return name.removesuffix(".json")
        d, source_id = read("wam/" + name)
        loader = d["dataloaders"]["train"]
        transform = loader["transform"]
        result = {"source_id": source_id, "history": clean_tuple(d["models"]["dynamic_history"]),
                  "train": select(d["train"], ["max_steps", "gradient_accumulation_steps", "mixed_precision", "with_ema"]),
                  "optimizer": select(d["optimizers"], ["type", "lr", "weight_decay"]),
                  "gpus": len(d["launch"]["gpu_ids"]), "batch_per_gpu": loader["batch_size_per_gpu"],
                  "history_frame_offsets": clean_tuple(transform["history_frame_offsets"]),
                  "history_recent_count": transform["history_recent_count"]}
        result["effective_batch"] = result["gpus"] * result["batch_per_gpu"] * result["train"]["gradient_accumulation_steps"]
        result["training_episode_range"] = select(loader["data_or_config"][0], ["episode_start", "episode_stop"])
        config_exports[name] = result
        memory_sources.add(source_id)
        return name.removesuffix(".json")

    def run(run_id, task, group, d, source_id, config_name=None, baseline_id=None):
        rows = d["episodes"]
        assert len(rows) == d["num_evals"] and len({r["layout_id"] for r in rows}) == len(rows)
        assert sum(r["success"] for r in rows) == d["successes"]
        assert abs(mean(r["score"] for r in rows) - d["mean_score"]) < 1e-9
        step_match = re.search(r"checkpoint_epoch_\d+_step_(\d+)", d["checkpoint"])
        item = {"run_id": run_id, "task": task, "group": group, "source_id": source_id,
                "checkpoint_step": int(step_match.group(1)) if step_match else None,
                "baseline_run_id": baseline_id, "config_id": config(config_name) if config_name else None,
                **select(d, ["stage", "num_evals", "successes", "success_rate", "mean_score", "num_workers",
                   "workers_per_gpu", "history_gate_scale", "history_output_gate_scale", "history_action_layers", "history_visual_layers"])}
        memory_runs.append(item)
        memory_sources.add(source_id)
        memory_episodes.extend({"run_id": run_id, "task": task, **select(e, ["layout_id", "success", "score", "env_steps"])} for e in rows)

    d, source_id = read("wam/memory-dynamic-paired.json")
    run("tower-base", "build_tower", "dynamic-20260813", d["baseline"], source_id)
    run("tower-late-initial", "build_tower", "dynamic-20260813", d["memory"], source_id,
        "memory-dynamic-config.json", "tower-base")
    d, source_id = read("wam/memory-injection-comparison.json")
    for name, row in d["variants"].items():
        cfg = "memory-early-action-config.json" if name == "early_a_4_8" else "memory-early-va-config.json" if name == "early_va_4_8" else "memory-dynamic-config.json"
        run("tower-" + name, "build_tower", "injection-20260813-16", row, source_id, cfg, "tower-base")
    zero = d["zero_gate_equivalence"]
    write("memory-zero-gate-audit.json", {"source_id": source_id,
        **select(zero, ["runtime_corrections_exact_zero", "runtime_action_delta_exact_zero"]),
        "checkpoint": select(zero["checkpoint"], ["comparison_contract", "baseline_tensors", "candidate_nonhistory_tensors",
            "matched_nonhistory_tensors", "candidate_history_tensors", "nonhistory_exact_after_dtype_cast", "mismatches"])}, [source_id])
    for name, run_id in [("memory-v2-off.json", "tower-v2-output-off"), ("memory-v2-on.json", "tower-v2-output-on")]:
        d, source_id = read("wam/" + name)
        run(run_id, "build_tower", "output-bridge-20260816", d, source_id, "memory-v2-config.json", "tower-base")
    d, source_id = read("wam/memory-token-comparison.json")
    for name, row in d["variants"].items():
        run("tower-" + name, "build_tower", "tokens-20260819-20", row, source_id,
            "memory-token" + str(int(name[-2:])) + "-config.json", "tower-base")
    for file, group in [("memory-four-tasks.json", "tasks-20260817"), ("memory-two-tasks.json", "tasks-20260818")]:
        d, source_id = read("wam/" + file)
        for task, comparison in d.items():
            base_id = task + "-base"
            run(base_id, task, group, comparison["baseline"], source_id)
            run(task + "-early-a", task, group, comparison["early_action_4_8"], source_id,
                "memory-dustbin-config.json" if task == "put_bottles_into_dustbin" else None, base_id)
    write("memory-runs.json", memory_runs, memory_sources, len(memory_runs))
    write("memory-episodes.csv", memory_episodes, memory_sources)
    write("memory-configs.json", {k.removesuffix(".json"): v for k, v in config_exports.items()},
          [v["source_id"] for v in config_exports.values()], len(config_exports))
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v["rows"] for k, v in manifest["exports"].items()}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    args = parser.parse_args()
    build(args.sources)
