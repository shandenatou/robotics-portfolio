# GWP 基线训练与评测

[首页](../../README.md) · [GWP RL](../gwp-rl/README.md) · [五任务原始汇总摘录](../../data/experiments/gwp-baseline-evals.json)

## RoboTwin：50-task SFT，五任务随机化测试

从 Giga-World-Policy-0.5 初始化，完成 RoboTwin 数据管线适配和多任务 SFT。每个训练任务含 50 条 clean 与 500 条 randomized 示范，总计 **50 个任务、27,500 条示范、6,077,247 帧**。

2026-07-22 对 **90K EMA checkpoint** 评测以下 5 个任务，每项 32 次，所有汇总的 client failure 均为 0。50 是训练任务数，不是本页已评测任务数。

| 任务 | 成功数 | 成功率 |
| --- | ---: | ---: |
| `stack_blocks_three` · 叠三块 | 24/32 | 75.00% |
| `stack_bowls_three` · 叠三碗 | 20/32 | 62.50% |
| `blocks_ranking_size` · 积木排序 | 18/32 | 56.25% |
| `place_dual_shoes` · 摆双鞋 | 15/32 | 46.88% |
| `open_microwave` · 开微波炉 | 6/32 | 18.75% |
| 本页五任务合计 | **83/160** | **51.88%** |

### 训练与部署配置

| 项目 | 配置 |
| --- | --- |
| 数据 | LeRobot v2.1 → 零拷贝 v3 兼容视图；复用源视频与 Parquet |
| 图像 | high / left wrist / right wrist，320×384 T-layout，Wan2.2 VAE |
| 状态与动作 | 16-D 双臂 EEF；平移、四元数相对当前状态，夹爪保留绝对值 |
| 归一化 | 全训练集 q01/q99，推理时反变换与训练表示一致 |
| 动作 horizon / 视觉 offsets | 48；0/12/24/36/48，源数据 50 Hz |
| 训练目标 | visual + action flow-matching |
| GPU / global batch | 4 × L20X / 64 |
| 学习率 / 优化器 / 精度 | 3e-5 / CAME8Bit / BF16；开启 EMA |
| 配方计划 / 本页评测权重 | 100K steps / 90K EMA |

部署端将相对平移和旋转还原成绝对 EEF 目标，避免混用 joint-delta 动作逆变换。这里记录的是已用 90K checkpoint 完成的评测，不据配方计划宣称 100K 全程已核验。

## 后续实验分别使用哪套基线

| 实验 | 环境与比较方式 | SFT 对照 | 记录 |
| --- | --- | --- | --- |
| 五任务能力测试 | RoboTwin randomized，每任务 32 次 | 上表 | [正式汇总](../../data/experiments/gwp-baseline-evals.json) |
| 叠碗 Q-gate | 固定背景，8 个 held-out 布局 × 4 次采样 | 26/32 | [配对 CSV](../../data/experiments/gwp-qgate-paired.csv) |
| 摆鞋 ActionExpert LoRA | 固定 64 seeds | 35/64 | [正式汇总](../../data/experiments/gwp-stage-f-evals.json) |
| 摆鞋早期 World-Preview | 另一组 64 场配对 | 34/64 | [配对 CSV](../../data/experiments/gwp-paired.csv) |
| RoboDojo 历史记忆 | 倒瓶入桶、搭塔，各 16 布局；另一套训练与环境协议 | 10/16、0/16 | [记忆实验](../long-horizon-memory/README.md) |

同一任务的分数会随背景、布局、采样和 checkpoint 协议改变。RL 的变化量只从本组对照计算；不能把随机化叠碗的 20/32 与固定背景 Q-gate 的 28/32 相减。
