# 结果索引

[首页](../README.md) · [完整实验数据](../data/experiments/README.md)

## 有提升的记录

| 任务 / 版本 | 对照 → 实验版 | 对应文件 |
| --- | --- | --- |
| 倒瓶入桶 / Early-A 4/8 | 10/16 → 12/16，阶段分 0.740625 → 0.831250 | [逐布局](../data/experiments/memory-episodes.csv)、[run 与配置](../data/experiments/memory-runs.json) |
| 搭塔 / V2 output OFF | 0/16 → 2/16，阶段分 0.050000 → 0.268750 | 同上，`tower-v2-output-off` |
| FastWAM 叠碗 / Update 40 | Randomized 41/50 → 44/50；Clean 38/50 → 39/50 | [6 行原汇总摘录](../data/experiments/fastwam-evals.csv) |

记忆结果来自逐布局评测汇总；FastWAM 是原表 `successes_est`，缺逐 episode 聚合。搭塔经历过同布局 probe 与选点，基线复用；尚无独立多训练种子重复。不同模型、任务、设置不合并为总提升。

## 其他记录

| 实验 | 结果 | 数据 |
| --- | --- | --- |
| LingBot Raw SFT / Exp005 | 都是 11/16 | [160 条评测，含其余 8 版](../data/experiments/lingbot-episodes.csv) |
| GWP World-Preview K4 | SFT 34/64，实验版 35/64；16 胜、15 负 | [64 场配对](../data/experiments/gwp-paired.csv) |
| 记忆扩展任务与消融 | 完整保留 24 组，包含收益、退化与零成功 | [运行索引](../data/experiments/memory-runs.json) |

失败原因与尚未验证的解释见[失败记录](failed-experiments.md)，不在主结果页展开。

## 可复算的部分

导入脚本按逐布局/逐 seed 字段重算成功数与均分，核对原汇总；绘图脚本只读取导出的 CSV。[来源哈希与字段说明](../data/experiments/README.md)

旧 [results.json](../data/results.json) 仍标为人工摘录，用于上一版 GWP 汇总图检查。新增记录不能称为“原始模拟器轨迹”或“本次复现结果”。
