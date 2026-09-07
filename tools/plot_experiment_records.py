"""Rebuild README figures from the exported experiment tables (stdlib only)."""
import csv
from html import escape
import json
from math import log10
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/experiments"
FIG = ROOT / "assets/diagrams"


def rows(name):
    with (DATA / name).open() as file:
        return list(csv.DictReader(file))


def text(x, y, value, size=15, color="#24292f", anchor="start"):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(str(value))}</text>'


def rect(x, y, w, h, color):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>'


def save(name, title, height, elements):
    content = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 {height}" role="img">'
               f'<title>{escape(title)}</title><g font-family="Arial, PingFang SC, sans-serif">'
               + rect(0, 0, 920, height, "#ffffff") + text(24, 34, title, 21)
               + "".join(elements) + '</g></svg>\n')
    (FIG / name).write_text(content)


def memory():
    records = rows("memory-episodes.csv")
    order = [("tower-base", "搭塔 · SFT"), ("tower-v2-output-off", "搭塔 · Early-A / 输出桥 OFF"),
             ("put_bottles_into_dustbin-base", "倒瓶入桶 · SFT"),
             ("put_bottles_into_dustbin-early-a", "倒瓶入桶 · Early-A")]
    elements = [text(24, 60, "每格为一个布局的阶段得分；完整结果保留在 memory-episodes.csv", 14, "#57606a")]
    for col in range(16):
        elements.append(text(298 + 36 * col, 94, col, 12, anchor="middle"))
    for i, (run_id, label) in enumerate(order):
        y = 110 + i * 59
        elements.append(text(24, y + 23, label, 14))
        selected = sorted([r for r in records if r["run_id"] == run_id], key=lambda r: int(r["layout_id"]))
        assert len(selected) == 16
        for j, row in enumerate(selected):
            score = float(row["score"])
            success = row["success"] == "True"
            color = "#0969da" if success else "#b6d7f8" if score > 0 else "#f0f2f4"
            elements += [rect(282 + 36*j, y, 33, 34, color),
                         text(298 + 36*j, y + 23, f"{score:g}", 12, "white" if success else "#24292f", "middle")]
    elements += [rect(24, 367, 16, 16, "#0969da"), text(48, 380, "成功", 13),
                 rect(120, 367, 16, 16, "#b6d7f8"), text(144, 380, "未成功，有阶段得分", 13),
                 text(24, 413, "同一任务内比较；每版 16 个布局。搭塔基线为复用记录，未在每轮重新运行。", 13, "#57606a")]
    save("memory-layout-scores.svg", "历史记忆：逐布局成绩", 438, elements)


def lingbot():
    records = rows("lingbot-episodes.csv")
    order = ["sft", "exp005", "exp008", "exp009", "exp010", "exp011", "exp012", "exp013", "exp014", "exp015"]
    seeds = sorted({r["seed"] for r in records if r["source"] == "sft"})
    elements = [text(24, 63, "同列对应同一 seed；中止计入未成功，不从分母里剔除。", 14, "#57606a")]
    for col in range(16):
        elements.append(text(177 + 36 * col, 93, col + 1, 12, anchor="middle"))
    for i, source in enumerate(order):
        y = 106 + 33 * i
        selected = {r["seed"]: r for r in records if r["source"] == source}
        assert set(selected) == set(seeds)
        elements.append(text(24, y + 20, source, 15))
        success = 0
        for j, seed in enumerate(seeds):
            row = selected[seed]
            yes = row["success"] == "True"
            success += yes
            elements.append(rect(162+36*j, y, 29, 25, "#0969da" if yes else "#eceff2"))
            if row["abortReason"]:
                elements.append(text(176+36*j, y+18, "×", 17, "#8a4600", "middle"))
        elements.append(text(767, y + 20, f"{success}/16", 15))
    elements += [text(24, 467, "蓝：成功　灰：未成功　×：规划失败中止。列号与完整 seed 对照见 CSV。", 13, "#57606a")]
    save("lingbot-seed-results.svg", "LingBot：10 版策略的 160 条评测", 491, elements)


def line_panel(elements, x, y, width, height, title, series, xmax, ymin, ymax, logarithmic=False):
    elements.append(text(x, y-14, title, 15))
    for j in range(5):
        value = ymin + (ymax-ymin)*j/4
        py = y + height - height*j/4
        elements += [f'<path d="M{x},{py} H{x+width}" stroke="#e5e7eb" fill="none"/>',
                     text(x-9, py+4, f"{10**value:.0e}" if logarithmic else f"{value:.3g}", 11, "#57606a", "end")]
    for j in range(5):
        px = x + width*j/4
        elements.append(text(px, y+height+23, f"{xmax*j/4:g}", 12, anchor="middle"))
    for label, color, values in series:
        points = []
        for step, val in values:
            val = log10(val) if logarithmic else val
            points.append((x+width*step/xmax, y+height-height*(val-ymin)/(ymax-ymin)))
        path = " ".join(("M" if i == 0 else "L") + f"{px:.2f},{py:.2f}" for i, (px, py) in enumerate(points))
        elements.append(f'<path d="{path}" stroke="{color}" stroke-width="1.7" fill="none"/>')
    for i, (label, color, _) in enumerate(series):
        elements += [rect(x+i*175, y+height+40, 15, 3, color), text(x+22+i*175, y+height+46, label, 12)]


def fastwam():
    rollouts, updates = rows("fastwam-rollouts.csv"), rows("fastwam-updates.csv")
    elements = [text(24, 61, "保留 41 条采样记录、40 次更新；折线连接原记录，不做平滑。", 14, "#57606a")]
    line_panel(elements, 74, 112, 355, 176, "训练采样 reward（不是独立评测成功率）",
               [("reward_mean", "#0969da", [(float(r["step"]), float(r["reward_mean"])) for r in rollouts if r["reward_mean"]])], 40, 0, 1)
    fields = [("更新前 sample KL", "#0969da", "sample_approx_kl"),
              ("更新后 sample KL", "#6e7781", "post_step_sample_approx_kl")]
    series = [(label, color, [(float(r["step"]), float(r[key])) for r in updates]) for label, color, key in fields]
    max_value = max(v for _, _, points in series for _, v in points)
    line_panel(elements, 535, 112, 355, 176, "Sample approximate KL", series, 40, 0, max_value*1.05)
    elements.append(text(24, 381, "横轴：update。缺失 reward 不绘点；Gaussian KL 另存 CSV，未与 sample KL 混画。", 13, "#57606a"))
    save("fastwam-training-records.svg", "FastWAM：Update 0–40", 406, elements)


def rl_cases():
    for exp in ("exp005", "exp010", "exp016"):
        records = rows(f"lingbot-{exp}-training.csv")
        xmax = max(int(r["step"]) for r in records)
        fields = [("score_min", "训练 batch 的保守进度分数"), ("kl_to_base", "预测 latent 相对锚点的 MSE")]
        if exp == "exp010":
            fields = [("loss_preference", "联合去噪偏好 loss"), ("loser_gradient_scale", "Loser 梯度缩放系数")]
        elements = [text(24, 61, f"{len(records)} 条原始训练标量；不平滑。环境成功率单列在 Results 中。", 14, "#57606a")]
        for x, (field, label) in zip((74, 535), fields):
            points = [(int(r["step"]), float(r[field])) for r in records]
            values = [value for _, value in points]
            low, high = min(0, min(values)), max(values)
            span = max(high-low, 0.01)
            line_panel(elements, x, 112, 355, 176, label,
                       [(field, "#0969da", points)], xmax, low-span*0.05, high+span*0.05)
        elements.append(text(24, 381, "横轴：optimizer step。训练目标值与独立环境评测成功率不是同一个指标。", 13, "#57606a"))
        save(f"lingbot-{exp}-training.svg", f"LingBot {exp.upper()}：训练记录", 406, elements)


def gwp():
    training = rows("gwp-training.csv")
    checkpoints = [r for r in rows("gwp-checkpoints.csv") if r["split"] == "validation"]
    elements = [text(24, 61, "301 条训练指标；右图为进入 checkpoint 选择的 7 组验证结果。", 14, "#57606a")]
    line_panel(elements, 78, 112, 350, 176, "Critic loss（对数纵轴）",
               [("critic/loss", "#0969da", [(float(r["step"]), float(r["critic/loss"])) for r in training])], 6000, -5, -1, True)
    line_panel(elements, 535, 112, 355, 176, "验证集：轨迹区分与同阶段排序",
               [("AUROC", "#0969da", [(float(r["checkpoint_step"]), float(r["auroc"])) for r in checkpoints]),
                ("最差阶段 pairwise", "#6e7781", [(float(r["checkpoint_step"]), float(r["same_stage_pairwise_min"])) for r in checkpoints])], 6000, 0, 1)
    elements.append(text(24, 381, "横轴：训练 step。选中 step 5000；独立测试与 64 场闭环评测另列，未用于此图的选点。", 13, "#57606a"))
    save("gwp-training-records.svg", "World-Preview：训练与 checkpoint 记录", 406, elements)


def gwp_value():
    training, validation = rows("gwp-value-training.csv"), rows("gwp-value-validation.csv")
    elements = [text(24, 61, "1500 步训练；31 次验证。选择 step 500，折线不平滑。", 14, "#57606a")]
    line_panel(elements, 78, 112, 350, 176, "World-Value training loss",
               [("train/loss", "#0969da", [(int(r["step"]), float(r["train/loss"])) for r in training])],
               1500, 0, max(float(r["train/loss"]) for r in training)*1.05)
    line_panel(elements, 535, 112, 355, 176, "验证集：真实 / 预测未来误差",
               [("real MAE", "#0969da", [(int(r["step"]), float(r["val/mae"])) for r in validation]),
                ("world MAE", "#6e7781", [(int(r["step"]), float(r["val/world_mae"])) for r in validation])],
               1500, 0, 0.4)
    elements.append(text(24, 381, "横轴：训练 step。在线 ASAR 为另一组 32 对 rollout，未画成训练成功率。", 13, "#57606a"))
    save("gwp-value-training.svg", "GWP World-Value：训练与验证", 406, elements)


if __name__ == "__main__":
    memory()
    lingbot()
    fastwam()
    rl_cases()
    gwp()
    gwp_value()
    print("Rebuilt 8 figures from CSV records.")
