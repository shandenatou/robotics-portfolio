# 实验数据

[首页](../../README.md) · [文件校验清单](manifest.json)

从服务器已有的 CSV、评测 JSON、指标 JSONL 中提取数值字段。2026-09-07 整理，没有重新训练或运行模拟器。服务器路径、账号链接、视频路径与提示词未导出。

## 历史记忆

| 文件 | 数量 | 内容 |
| --- | ---: | --- |
| [memory-runs.json](memory-runs.json) | 24 组 | task、run ID、checkpoint step、配置 ID、评测数、成功数、均分 |
| [memory-episodes.csv](memory-episodes.csv) | 384 行 | 每个 run 的 layout、success、score、env_steps |
| [memory-configs.json](memory-configs.json) | 9 份 | 历史结构、层号、batch、学习率、精度、训练范围 |
| [memory-zero-gate-audit.json](memory-zero-gate-audit.json) | 1 份 | 1664 个非历史张量的 dtype 对齐检查、运行时零残差检查 |

`run_id` 是本次整理使用的短 ID；`stage` 保留原评测阶段名。搭塔基线只导出一份，复用关系见 `baseline_run_id`，384 行不含跨汇总重复引用的基线。其他任务各有自己的基线，不合并计分。

`score` 是任务评测器原始阶段得分，和二元 `success` 分开。不同任务的 score 定义不保证相同。配置缺失时 `config_id=null`，没有猜测补全。运行时 `history_output_gate_scale` 优先于训练配置；V2 的 OFF/ON 使用同一个 checkpoint。

## FastWAM

| 文件 | 行数 | 内容 |
| --- | ---: | --- |
| [fastwam-evals.csv](fastwam-evals.csv) | 6 | Base / u30 / u40 × random / clean |
| [fastwam-updates.csv](fastwam-updates.csv) | 40 | 更新前后 KL、policy loss、grad norm、active rank、耗时 |
| [fastwam-rollouts.csv](fastwam-rollouts.csv) | 41 | 采样数、reward、采样成功率 |

`successes_est` 是原表字段，不是经逐 episode 重算的成功数。step 40 的 rollout reward 为空，表示没有采样，不补为 0。CSV 空格表示原记录缺失；`run` 区分 0–30 与 30–40 两段。

## LingBot

| 文件 | 行数 | 内容 |
| --- | ---: | --- |
| [lingbot-runs.csv](lingbot-runs.csv) | 10 | 每版成功数、中止数，由 episode 表计算 |
| [lingbot-episodes.csv](lingbot-episodes.csv) | 160 | run、seed、success、abortReason、chunk 数、进度校正量 |
| [lingbot-action-audit.csv](lingbot-action-audit.csv) | 32 | Raw SFT / Exp005 的动作与执行审计 |
| [lingbot-ruler-eval.json](lingbot-ruler-eval.json) | 4 workers | 7 月 9 日版本的完成数、成功数和缺失数 |
| [lingbot-formal-evals.json](lingbot-formal-evals.json) | 4 runs | Exp005 / 007 / 010 / 016 的正式 4-worker 摘要 |
| [lingbot-selected-configs.json](lingbot-selected-configs.json) | 3 份 | Exp005 / 010 / 016 的字段白名单配置，含 LoRA 目标模块 |
| [lingbot-exp005-training.csv](lingbot-exp005-training.csv) | 1500 | 每步进度分数、latent MSE、梯度范数、学习率 |
| [lingbot-exp010-training.csv](lingbot-exp010-training.csv) | 1000 | 偏好 loss、候选统计、梯度夹角与缩放、参考 / 当前去噪误差 |
| [lingbot-exp016-training.csv](lingbot-exp016-training.csv) | 1500 | 后层 LoRA 的每步进度分数、latent MSE、梯度范数、跳步计数 |

正式摘要独立于审阅集文件，但 Exp005 / Exp010 描述同一批评测，不按两份文件重复计样本。Exp007 / Exp016 没有逐 episode 导出，只保留 worker 汇总；摘要中 `completed=expected=episodes=16`，不能由此推断规划失败次数为 0。

三个训练 CSV 每行对应一个成功 optimizer step，保留原标量字段。`kl_to_base` 是 latent MSE 代理，不是解析 KL；训练 reward / preference loss 不替代环境成功率。

160 行来自当时的视频审阅集元数据，32 行来自事后动作审计，不能称为原始模拟器日志。不同表用 episode ID / seed 对应，不将“动作条数”和“episode 数”混计。中止仍在评测分母内；没有中止不等于没有规划失败。

`elapsed_sec` 为运行耗时，`take_action_count` 为执行次数；`numSteps` / `num_replans` 是重规划层面的计数。动作差分指标沿用原审计定义，不能直接当作真实机器人加速度、jerk 或硬件速度。

## GWP 候选动作评价

### 叠碗 Q / Value 引导与基线

| 文件 | 数量 | 内容 |
| --- | ---: | --- |
| [gwp-qgate-paired.csv](gwp-qgate-paired.csv) | 32 对 | 初始 8 对 + 扩展 24 对，layout、repeat、两侧成败；合计 26 → 28 |
| [gwp-asar-paired.csv](gwp-asar-paired.csv) | 32 对 | 旧 Q / World-Value + ASAR，合计 23 → 27 |
| [gwp-bowls-experiments.json](gwp-bowls-experiments.json) | 1 份 | 分阶段汇总、配对检验、Value 配置和 step 500 指标 |
| [gwp-value-training.csv](gwp-value-training.csv) | 1500 行 | 每个 optimizer step 的原始训练标量 |
| [gwp-value-validation.csv](gwp-value-validation.csv) | 31 行 | step 1 及每 50 步验证；验证轨迹不作为在线 rollout |
| [gwp-baseline-evals.json](gwp-baseline-evals.json) | 5 个任务 | 90K SFT 五任务随机化评测，160 次；保留 worker 汇总 |
| [gwp-stage-f-evals.json](gwp-stage-f-evals.json) | 2 版 | 摆鞋 SFT / ActionExpert LoRA，各 64 次；worker 汇总 |
| [gwp-mc-q-config.json](gwp-mc-q-config.json) | 1 份 | 实际部署的 MC-return Twin-Q 输入、正式参数、门控和最终指标 |
| [gwp-mc-q-training.csv](gwp-mc-q-training.csv) | 51 行 | 1000 步训练中的 step 1 与每 20 步训练/验证标量 |

Q-gate 的 `repeat=0` 是最初试验，1/2/3 是扩展采样，不是 32 个独立布局。扩展 24 对为 21/24 → 21/24；32 对合计收益包含初测。ASAR 是另一组对照，不能与 Q-gate 拼成四臂配对。

五任务随机化基线与叠碗固定背景对照不可互换。正式 summary 的 worker 完成数、成功数与总数均在提取时核对；未包含原始模拟器轨迹。

具体方法分别见 [MC-return 双 Q 与门控](../../projects/gwp-rl/experiments/mc-return-q-gate.md)、[历史条件 Value 与 ASAR](../../projects/gwp-rl/experiments/world-value-asar.md)。双 Q 的 no_interactions 版本不读取语言；MC-return λ=1 与运行时门控是两个不同设置。

### 早期摆鞋 World-Preview

| 文件 | 行数 | 内容 |
| --- | ---: | --- |
| [gwp-paired.csv](gwp-paired.csv) | 64 | 同 seed 的 SFT / World-Preview 成败和中止 |
| [gwp-training.csv](gwp-training.csv) | 301 | step 1–6000 的数值训练记录 |
| [gwp-checkpoints.csv](gwp-checkpoints.csv) | 8 | 7 个候选的 validation，另加 step 5000 的 test |
| [gwp-branch-gate.json](gwp-branch-gate.json) | 1 份 | 分支数据接受/拒绝数、阈值、偏好对与 split 覆盖 |

训练每隔若干步记录一次，301 行不表示训练只有 301 steps。Checkpoint 表来自“eligible”候选清单，并非所有保存的 checkpoint；选择使用 validation，test 单列，闭环 64 场评测不混入离线分类指标。

## 来源和复算

[manifest.json](manifest.json) 保存每份原文件的 SHA-256、大小，以及导出文件的行数和哈希。原文件在私有审阅目录中，哈希只用于追溯本次提取，不能代替原始轨迹或公开许可。

`tools/import_experiment_records.py` 按字段提取、从逐场景记录重算成功数与均分，再与原汇总核对。图表由 `tools/plot_experiment_records.py` 从这些导出表生成。

原有 [results.json](../results.json) 是上一版人工摘录，供旧图校验使用；新增的逐场景记录在本目录。未取回的 temporal K4/K8 成功数仍只有报告支持。
