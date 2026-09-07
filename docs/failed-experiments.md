# 关键消融与失败简表

[首页](../README.md) · [完整数据](../data/experiments/README.md)

只保留影响方法选择的几项。完整数值留在数据文件，不逐版重复说明；未隔离验证的原因标为推测。

## 历史记忆

| 实验 | 结果 | 原因或现象 |
| --- | --- | --- |
| 4/8 层双分支 | 0/16，均分 0.075；仅动作版 1/16、0.2125 | 视频分支没有带来收益，保留仅动作注入；具体原因未隔离。 |
| V2 右臂输出桥 | ON 1/16，OFF 2/16；同 checkpoint | 观察：OFF 的两个成功布局在 ON 下丢失，ON 新增一个成功；轨迹确实改变，整体变差。 |

[全部记忆实验数据](../data/experiments/memory-runs.json)

## LingBot

| 实验 | 成功数 | 原因或现象 |
| --- | ---: | --- |
| Exp009 · K2 偏好训练 | 4/16 | 日志诊断：相对偏好 margin 可通过增大 loser 去噪误差改善，后期 video/action MSE 对参考模型的偏离增加。 |
| Exp012 · 全参数进度 RL | 2/16 | SFT 上直接优化进度出现退化；限制到后层 LoRA 并调整学习率后为 10/16。共享表示受损是推测。 |

改动后的结果见 [Exp010](../projects/reward-action-alignment/experiments/exp010-preference.md) 与 [Exp016](../projects/reward-action-alignment/experiments/exp016-lora.md)。[全部逐 seed 数据](../data/experiments/lingbot-episodes.csv)

## FastWAM 与 GWP

| 实验 | 结果 | 原因或现象 |
| --- | --- | --- |
| FastWAM Update 30 | 77/100，Base 79/100 | 原因未定；旧表仍缺原始逐 episode 聚合。 |
| GWP ActionExpert LoRA | 35/64 → 36/64；修复 10、退化 9 | 动作漂移 6.44% 超过 3% 门限；Q 增益未稳定转成任务增益。 |

[GWP 的有效结果与配对数据](../projects/gwp-rl/README.md)
