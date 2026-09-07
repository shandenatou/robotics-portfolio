# 实验时间线

[首页](../README.md) · [数据目录](../data/experiments/README.md)

日期来自历史报告和运行目录。不同模型、任务间的切换不是受控消融。

| 时间 | 实验 | 后续改动与结果 | 记录 |
| --- | --- | --- | --- |
| 6 月 | FastWAM 去噪轨迹接入 actor 更新 | 叠碗 Update 30 为 77/100，Update 40 为 83/100，Base 79/100 | [40 次更新](../data/experiments/fastwam-updates.csv) |
| 7 月 9 日 | LingBot 成功示范阶段标签 | step 1500 为 6/16，低于 Base 9/16 | [完整完成数与 worker 结果](../data/experiments/lingbot-ruler-eval.json) |
| 7 月 13–20 日 | LingBot 进度训练、候选偏好、执行校准 | Raw SFT / Exp005 并列 11/16；Exp010 相对 Exp009 从 4/16 到 6/16 | [10 版、160 条评测](../data/experiments/lingbot-episodes.csv) |
| 7 月 17 日起的 LoRA 运行 | 冻结 SFT，仅更新后 4 个共享 block 的 rank-8 LoRA | Exp016 10/16；全参数 Exp012 2/16，Raw SFT 11/16；学习率也有变化 | [1500 步记录与正式汇总](../projects/reward-action-alignment/experiments/exp016-lora.md) |
| 7 月 22 日基线评测 | GWP 50-task SFT，90K EMA | 五任务各 32 次，共 83/160；不是 50 个任务都已评测 | [GWP 基线](../projects/gwp-baselines/README.md) |
| 7 月 26 日起的运行 | GWP temporal / World-Preview 候选排序 | K4/K8 旧重排退化；真实分支数据不足；World-Preview 35/64 对 SFT 34/64 | [训练与配对结果](../projects/world-preview-action-selection/README.md) |
| 8 月 2 日 | GWP ActionExpert LoRA 策略更新 | 固定 seed 的摆鞋 35/64 → 36/64，Q + action flow 锚点 | [策略与正式记录](../projects/gwp-rl/README.md#actionexpert-lora) |
| 8 月 5 日 | 叠碗 Twin-Q 保守动作选择 | 原策略 26/32 → 28/32；包含初测 8 对和扩展 24 对 | [Q-gate 配对](../projects/gwp-rl/README.md#q-gate) |
| 8 月 6 日 | 叠碗 World-Value + ASAR | 相对 MC-return Twin-Q＋ASAR：23/32 → 27/32；双方固定 16 候选和相同重构 | [方法、基线与 32 对记录](../projects/gwp-rl/experiments/world-value-asar.md) |
| 8 月 13–16 日 | GWP 搭塔历史注入 | 从 12/24 层双分支改为 4/8 层动作分支；Early-A 首轮 1/16，均分 0.2125 | [注入位置对照](../projects/long-horizon-memory/README.md#中间实验) |
| 8 月 16 日起的 V2 运行 | 增加右臂输出桥，并做同 checkpoint ON/OFF | OFF 2/16、ON 1/16；保留 OFF 成功布局 4、10 | [方法与配置](../projects/long-horizon-memory/README.md) |
| 8 月 17–18 日起的任务扩展 | Early-A 4/8 用于六个任务 | 倒瓶入桶 10/16 → 12/16；其他任务没有出现同样收益 | [全部运行](../data/experiments/memory-runs.json) |
| 8 月 19–20 日 | 4/8/16/32 token 消融 | 都是 0/16，8-token 重训也未复现先前收益 | [逐布局记录](../data/experiments/memory-episodes.csv) |

## 搭塔版本的关系

1. 原始 12/24 层历史模块在环境里有非零残差，但没有成功；随后把注入位置移到更早的 4/8 层，并拆开动作 / 视频分支。
2. 仅动作分支得到首个成功。门控扫描改变了成功布局，仍未解决整体成功率低的问题。
3. 右臂输出桥针对当时动作干预左右不均的观察；同 checkpoint 关闭输出桥的结果更好，因此 2/16 不能记为桥接收益。
4. 扩展任务和 token 消融分别保留。倒瓶入桶的收益没有在所有任务、所有重训版本上重现。

[失败原因简表](failed-experiments.md)
