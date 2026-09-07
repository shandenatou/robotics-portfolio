"""Build static, source-grounded diagrams for GitHub Markdown."""
from html import escape
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "assets/diagrams"


def wrap(text, limit):
    """Wrap CJK characters and English words using conservative width units."""
    tokens = re.findall(r"[A-Za-z0-9_./+-]+|.", text)
    lines, current, size = [], "", 0
    for token in tokens:
        cost = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in token)
        if current and size + cost > limit:
            lines.append(current.strip())
            current, size = "", 0
        current += token
        size += cost
    if current.strip():
        lines.append(current.strip())
    return lines


def save(name, title, width, height, parts):
    content = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'
        f'<title>{escape(title)}</title><desc>方法示意；灰色为输入或冻结模块，蓝色为本实验学习的模块。各阶段的更新范围见标题。</desc>'
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#57606a"/></marker></defs>'
        f'<rect width="{width}" height="{height}" fill="#fff"/>'
        '<g fill="#1f2328" font-family="Arial, PingFang SC, sans-serif">'
        + ''.join(parts) + '</g></svg>\n')
    (FIG / name).write_text(content)


def flow(name, title, sections, footer):
    width, margin, gap = 960, 24, 30
    parts, y = [], 32
    for heading, boxes in sections:
        parts.append(f'<text x="24" y="{y}" font-size="19" font-weight="600">{escape(heading)}</text>')
        y += 18
        for start in range(0, len(boxes), 3):
            row = boxes[start:start+3]
            card_width = (width-2*margin-(len(row)-1)*gap)/len(row)
            line_limit = int((card_width-32)/9.2)
            texts = [(wrap(lead, line_limit), wrap(sub, line_limit+3), kind) for lead, sub, kind in row]
            height = max(30+len(lead)*24+len(sub)*23+14 for lead, sub, _ in texts)
            for index, (lead, sub, kind) in enumerate(texts):
                x = margin+index*(card_width+gap)
                fill = "#eef6ff" if kind == "train" else "#f6f8fa"
                parts.append(f'<rect x="{x}" y="{y}" width="{card_width}" height="{height}" rx="4" fill="{fill}" stroke="#d0d7de"/>')
                line_y = y+29
                for line in lead:
                    parts.append(f'<text x="{x+16}" y="{line_y}" font-size="18" font-weight="600">{escape(line)}</text>')
                    line_y += 24
                line_y += 5
                for line in sub:
                    parts.append(f'<text x="{x+16}" y="{line_y}" font-size="16" fill="#57606a">{escape(line)}</text>')
                    line_y += 23
                if index < len(row)-1:
                    parts.append(f'<path d="M{x+card_width+4} {y+height/2} H{x+card_width+gap-4}" stroke="#57606a" stroke-width="1.5" fill="none" marker-end="url(#arrow)"/>')
            if start+3 < len(boxes):
                next_count = min(3, len(boxes)-start-3)
                next_width = (width-2*margin-(next_count-1)*gap)/next_count
                last_x = margin+(len(row)-1)*(card_width+gap)+card_width/2
                first_x = margin+next_width/2
                parts.append(f'<path d="M{last_x} {y+height+2} V{y+height+18} H{first_x} V{y+height+33}" stroke="#57606a" stroke-width="1.5" fill="none" marker-end="url(#arrow)"/>')
                y += height+38
            else:
                y += height+42
    for paragraph in footer:
        for line in wrap(paragraph, 100):
            parts.append(f'<text x="24" y="{y}" font-size="16" fill="#57606a">{escape(line)}</text>')
            y += 24
    save(name, title, width, y+8, parts)


def overview():
    parts = []
    def text(x, y, value, size=17, weight="400", fill="#1f2328"):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(value)}</text>')
    def card(x, y, lines, train=False):
        parts.append(f'<rect x="{x}" y="{y}" width="360" height="78" rx="4" fill="{"#eef6ff" if train else "#f6f8fa"}" stroke="#d0d7de"/>')
        for i, line in enumerate(lines):
            text(x+16, y+30+i*26, line, 17 if i==0 else 16, "600" if i==0 else "400")
    def arrow(y, label):
        parts.append(f'<path d="M400 {y} H550" stroke="#57606a" stroke-width="1.5" fill="none" marker-end="url(#arrow)"/>')
        text(411, y-13, label, 15, fill="#57606a")
    text(24, 32, "共同基础：GWP-0.5 · 50-task SFT · 90K EMA（冻结）", 20, "600")
    text(24, 74, "实验一：增加选择器 · 4 个候选", 18, "600")
    card(24, 90, ["基线：直接执行 candidate 0", "不按 Q 分数换动作"])
    card(568, 90, ["改进：MC-return Twin-Q 门控", "两 Q 认可增益且分歧小，才替换"], True)
    arrow(132, "增加双 Q 与门控")
    text(24, 212, "实验二：替换评分器 · 16 个候选 · 双方均使用 ASAR", 18, "600")
    card(24, 228, ["基线：MC-return Twin-Q", "Q 排序 → ASAR 邻域重构"])
    card(568, 228, ["改进：历史条件 Value", "预测进度排序 → 相同 ASAR 重构"], True)
    arrow(270, "只替换评分器")
    text(24, 347, "两组各自配对评测；实验二不继承实验一的门控，也不共用其对照成功率。", 16, fill="#57606a")
    save("gwp-action-guidance-method.svg", "GWP 两个实验各自的基线、改动与控制变量", 960, 368, parts)


def build():
    overview()
    flow("gwp-mc-q-method.svg", "Monte-Carlo return Twin-Q 与门控", [
        ("离线训练：更新 Q1 / Q2，冻结 GWP", [
            ("完整成功 / 失败 rollout", "终局成功奖励；反向累计 γ=0.99 的 MC return", "frozen"),
            ("编码当前视觉、预测未来、动作和状态", "512 + 512 + 256 + 128 → 1408 维特征", "train"),
            ("两个 Q 网络分别拟合相同回报目标", "Huber(Q1, G) + Huber(Q2, G)；1000 步", "train"),
        ]),
        ("在线执行：不更新参数", [
            ("GWP 生成 4 个候选及对应预测未来", "Q1 / Q2 对每个动作的前 12 步评分", "frozen"),
            ("双 Q 增益均 ≥ 0.001，分歧 ≤ 0.08", "满足门限：替换；否则执行原 candidate 0", "frozen"),
        ]),
    ], ["Q 的此版本不输入语言；指令仍用于 GWP 生成。", "视觉编码器从进度评价器初始化，随 Q 一起训练。"])
    flow("gwp-history-value-method.svg", "历史 Value 与 ASAR", [
        ("离线训练：更新历史聚合与 Value head", [
            ("最近 5 步：视觉 latent ＋ 16 维状态", "冻结视觉编码器 → 两层时序 Transformer", "train"),
            ("预测 256-bin 剩余时间进度分布", "失败轨迹增加 35-chunk 惩罚，标签裁剪到 [0,1]", "train"),
            ("同时监督真实后继与 World 预测后继", "分布交叉熵 ＋ Value 一致性 ＋ 进度差约束", "train"),
        ]),
        ("在线执行：冻结 Value 与 GWP", [
            ("16 个动作 → 16 个预测未来", "按 ΔV = V(预测未来) − V(当前) 排序", "frozen"),
            ("ASAR：High 8 中找局部高密度邻域", "稳健标准化 → 中心 / 邻居 → 加权重构动作", "frozen"),
            ("执行前 12 步，获取新观测后重规划", "旋转做四元数对齐，夹爪状态跟随中心候选", "frozen"),
        ]),
    ], ["图中 Value 不直接读取候选动作；动作通过预测未来影响评分。"])
    flow("fastwam-flow-grpo-method.svg", "FastWAM Flow-GRPO 后训练", [
        ("策略更新与环境采样", [
            ("FastWAM 动作生成与环境 rollout", "同一采样组保留候选动作及回报", "frozen"),
            ("保存动作去噪轨迹 sidecar", "按 trace ID 关联 rollout 与训练 bundle", "frozen"),
            ("由组内回报计算 advantage", "把连续动作去噪轨迹交给 actor worker", "train"),
            ("Flow-GRPO 更新策略参数", "记录 policy loss、梯度与更新前后 KL", "train"),
            ("更新后的策略进入下一轮 rollout", "独立评测 Clean / Randomized 叠碗成功率", "frozen"),
        ]),
    ], ["图示为实际桥接流程；训练曲线和评测在实验记录中分列。"])
    flow("lingbot-progress-rl-method.svg", "LingBot 完整去噪进度 RL", [
        ("训练输入：50 条成功示范中的当前状态", [
            ("同一输入、同一初始噪声", "可训练策略与冻结 Base 各执行完整 4 步去噪", "frozen"),
            ("策略生成 z_pred；Base 生成 z_anchor", "评分对象为 decoder 前的 clean future latent", "train"),
            ("三个冻结进度评价器取最小值", "reward = min(E1, E2, E3)(z_now, z_pred)", "frozen"),
            ("反传进度奖励，约束预测偏离", "loss = −reward + 0.10 latent MSE + 0.05 方差", "train"),
            ("更新共享 Transformer", "训练 1500 步，再做机器人闭环任务评测", "train"),
        ]),
    ], ["此路线没有显式动作奖励；动作通过共享参数间接改变。"])
    flow("memory-early-action-method.svg", "GWP 分层历史记忆与动作注入", [
        ("在线历史读取", [
            ("保存过去重规划时的视觉 token", "近期 3 次保留完整 token；更早历史分层压缩", "frozen"),
            ("当前观察查询历史 bank", "读出 8 个、每个 512 维的 memory token", "train"),
            ("注入 ActionExpert 第 4、8 层", "门控残差读取历史；视觉分支不注入", "train"),
            ("冻结 GWP 主干完成动作预测", "预测 48 步，执行前 12 步，再读取新观测", "frozen"),
        ]),
    ], ["训练历史模块时主干冻结；推理时整个模型冻结。", "搭塔展示结果关闭右臂输出桥，只使用 Early-A 路径。"])
    flow("gwp-action-lora-method.svg", "World-Q 奖励下的 ActionExpert LoRA", [
        ("训练：只更新 ActionExpert 的 LoRA 参数", [
            ("冻结 SFT 主干 + rank-8 Action LoRA", "30 个动作 block；注意力 Q/K/V 与输出映射", "train"),
            ("生成动作 → 冻结 World 预测未来", "action / world 各 10 步采样", "frozen"),
            ("冻结 Twin-Q 评分动作与预测未来", "reward = min(Q1, Q2)", "frozen"),
            ("奖励反传到 LoRA，保持行为锚点", "loss = −mean(reward) + 0.1 action flow loss", "train"),
            ("选定 checkpoint 后冻结全部参数评测", "固定 64 个 seed，统计修复与退化的任务数", "frozen"),
        ]),
    ], ["Self-attention 使用 Q/K/V/output；", "Cross-attention 仅用 Q/output，K/V 来自冻结视觉分支。"])
    print("Rebuilt 7 method diagrams.")


if __name__ == "__main__":
    build()
