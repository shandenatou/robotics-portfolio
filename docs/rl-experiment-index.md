# RL 与奖励后训练实验索引

[首页](../README.md) · [LingBot 总表](../projects/reward-action-alignment/README.md) · [实验数据](../data/experiments/README.md)

首页选择有明确结果的几项案例。这里保留其他路线，不将 weighted BC、候选重排和实际策略更新混成同一种 RL。

## 路线与对应记录

| 路线 | 实际改动 | 记录入口 |
| --- | --- | --- |
| FastWAM Flow-GRPO | 动作去噪轨迹、组内 advantage、actor/rollout 桥接 | [40 次更新与独立评测](../projects/fastwam-policy-optimization/README.md) |
| GWP Q-gate | 冻结 50-task SFT / 90K EMA，增加 MC-return 双 Q 门控 | [无选择器 26/32 → 门控 28/32](../projects/gwp-rl/experiments/mc-return-q-gate.md) |
| GWP World-Value + ASAR | 固定 16 候选＋ASAR，只把 MC-return Q 换成历史 Value | [Q＋ASAR 23/32 → Value＋ASAR 27/32](../projects/gwp-rl/experiments/world-value-asar.md) |
| LingBot 阶段加权 | 真实成功示范内部生成标签，weighted BC；RL 前置探索 | [阶段标签](../projects/reward-action-alignment/README.md#早期阶段标签版本) |
| LingBot 预测进度 RL | 对模型生成的未来 latent 评分并反传 | [Exp005：结果、1500 步训练与后续失败](../projects/reward-action-alignment/experiments/exp005-progress-rl.md) |
| LingBot 候选偏好 | 同状态 K2 候选、联合去噪偏好、loser 梯度保护 | [Exp010：4/16 → 6/16](../projects/reward-action-alignment/experiments/exp010-preference.md) |
| LingBot 执行校准 | 80 个 rollout、1472 条对齐 transition，校准预测与真实执行差异 | [Exp011 与失败记录](failed-experiments.md#lingbot) |
| LingBot 更新约束 | SFT 初始化、联合信任域、示范进度匹配、后层 LoRA | [Exp012–016；LoRA 恢复至 10/16](../projects/reward-action-alignment/experiments/exp016-lora.md) |
| LingBot 残差 actor-critic | 冻结 SFT，1392 条可用 transition，训练 bounded residual actor + twin-Q | [Exp015：7/16](#残差-actor-critic) |
| GWP World-Preview | Bellman 训练 Q、预测未来评分、候选动作重排 | [训练与 64 场配对](../projects/world-preview-action-selection/README.md) |
| GWP World / Action 联合 RL | 更新 World LoRA、Twin-Q/V、ActionExpert LoRA，闭环 replay | [多轮与 ActionExpert 记录](#gwp-策略更新与多轮实验) |

## LingBot 版本记录

<details>
<summary>展开版本、结果与来源</summary>

| 版本 | 训练路径 | 结果 / 状态 | 结果来源 |
| --- | --- | --- | --- |
| 7 月 9 日阶段标签 | success-demo-only 阶段与时间成本加权 | 6/16；后续弱负样本 / 时间成本版本未超过 Base | [独立 worker 汇总](../data/experiments/lingbot-ruler-eval.json) |
| Exp001 | learned evaluator 给 demo 加权 | 6/16；属于 weighted BC | 历史报告 |
| Exp002 | positive 35% → 45%，neutral weight 0.35 → 0.25 | 路线纠正后停止继续评测 | 历史报告，无最终能力结果 |
| Exp003 | 单步 x0 预测 latent 进度优化 | 1500 steps 完成，缺正式任务评测 | 历史报告 |
| Exp005 | 完整 4 步去噪的进度 RL | **11/16** | [正式汇总](../data/experiments/lingbot-formal-evals.json) + 逐 seed 审阅集 |
| Exp006 | 25 video / 50 action 的完整反传 | 指标前因 OOM / 兼容性停止 | 历史错误记录，不计为策略失败 |
| Exp007 | 25 步前向，仅末 4 步反传 | **8/16** | [正式汇总](../data/experiments/lingbot-formal-evals.json) |
| Exp008 | SFT 初始化 + 不确定性门控 | 5/16 | [逐 seed 表](../data/experiments/lingbot-episodes.csv) |
| Exp009 | Reference-relative K2 联合偏好 | 4/16 | 同上 |
| Exp010 | Loser 梯度保护 | **6/16** | [正式汇总](../data/experiments/lingbot-formal-evals.json) + 逐 seed 表 |
| Exp011 | Rollout 校准 + winner-only 蒸馏 | 5/16 | 逐 seed 表 |
| Exp012 | SFT 初始化 + 原 Exp005 目标 | 2/16 | 逐 seed 表 |
| Exp013 | 联合 video/action 信任域 | 3/16 | 逐 seed 表 |
| Exp014 | 示范进度匹配 + 联合信任域 | 1/16 | 逐 seed 表 |
| Exp015 | Latent residual actor-critic | 7/16 | 逐 seed 表 |
| Exp016 | 后 4 blocks、rank-8 LoRA | **10/16** | [正式汇总](../data/experiments/lingbot-formal-evals.json)，旧报告摘要解析失败已纠正 |

目前材料中没有 Exp004 的明确记录，编号空缺不补成实验。Raw SFT 是单独的 11/16 对照。四份正式汇总中的 Exp005 / Exp010 与原 160 条审阅集有重叠，不能把它们相加当成新增独立样本。

</details>

## 残差 actor-critic

Exp015 从 80 个真实 rollout 对齐出 1472 条 transition，剔除缺少 pre-action proprio 的 80 个首 chunk，使用剩余 **1392 条**。首个在线 chunk 同样不施加残差。

```text
a_actor = a_SFT + 0.1 * tanh(delta)
L_actor = 5.0 * MSE(a_actor, a_SFT) - 0.1 * Q1(s, a_actor)
```

Critic 预热 500 步，共训练 3000 步；gamma=0.96，Polyak tau=0.005，batch 128/GPU × 4。结果为 7/16，低于 SFT 的 11/16。报告中的动作均值步幅 0.002759 → 0.006708、jerk 0.002591 → 0.018080，说明动作变化明显增大；不能仅凭正的离线 Q gain 宣称策略收益。

## GWP 策略更新与多轮实验

下表来自各自运行报告，评测协议不同，不与早期 World-Preview 的 SFT 34/64 混用。

| 路线 | 实施内容 | 已记录结果 / 范围 |
| --- | --- | --- |
| World consistency | 真实 +12 步后继；VisualExpert LoRA、EMA World，再训练 Q / Actor | 19238 条初始 transition；旧 latent-noise proxy 的预测收益未转成 Action-Q 收益 |
| Stage-F ActionExpert LoRA | 30 个 ActionExpert block 的注意力 LoRA，5.90M 参数，Q + flow-matching 锚点 | **SFT 35/64 → LoRA 36/64**；修复 10、退化 9，McNemar p=1.0；离线漂移门限未通过 |
| 五轮闭环方案 | World → 缓存预测 → Q/V → Action LoRA → rollout → replay | 第 1 轮 36/64，与初始 36/64 持平；两轮使用不同 seeds，不作配对收益 |
| Entropy fast loop | 5 个 8-episode cycle | 5/8、4/8、5/8、1/8、1/8；已查明数据划分与发布门控缺陷，修正版结果未纳入 |
| SAC-Flow 风格 Scheme 3 | Action LoRA + bounded noise actor + soft twin-Q | 第 1 轮 World500、Q1000/A200 完成，30/64；不是五轮完成结果 |

GWP 的主要结果见 [Q / Value 引导与策略后训练](../projects/gwp-rl/README.md)，SFT 训练与已测任务见 [GWP 基线](../projects/gwp-baselines/README.md)。多轮方案不按计划轮数计为已完成实验。

[失败原因简表](failed-experiments.md) · [训练源码与公开范围](reproduction-status.md) · [报告来源哈希](../data/experiments/manifest.json)
