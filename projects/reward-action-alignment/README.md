# LingBot：预测进度奖励与策略更新约束

[首页](../../README.md) · [完整版本索引](../../docs/rl-experiment-index.md)

在放面包入篮任务中，完整去噪进度奖励版本达到 **11/16**，原始 Base 为 9/16，另训的 SFT 对照也是 11/16。围绕这条奖励路径，测试了候选偏好、更新范围与动作约束。

## 完整去噪进度奖励

![LingBot 预测进度 RL](../../assets/diagrams/lingbot-progress-rl-method.svg)

输入为成功示范中的当前状态。可训练策略和冻结 Base 使用同一初始噪声，分别完成 4 步去噪；三个冻结评价器对策略生成的未来 latent 评分，取最小值作为奖励。

loss 由负进度奖励、相对 Base 的 latent MSE 与评价器方差组成。梯度经过完整去噪链路更新共享 Transformer。这个版本没有显式 action loss，动作能力随共享参数间接变化。

## 后续方法

| 方法 | 具体改动 | 结果与记录 |
| --- | --- | --- |
| 完整去噪进度 RL | 单步估计改为 scheduler 终点评分，加入锚点和分歧约束 | [Base 9/16 → 11/16](experiments/exp005-progress-rl.md) |
| 候选偏好梯度保护 | 同状态生成两个候选，按三评价器一致排序训练；根据梯度夹角缩放 loser 分支，保护 winner | [4/16 → 6/16](experiments/exp010-preference.md) |
| 后层 LoRA | 冻结 SFT，只训练末 4 个共享 block 的 rank-8 LoRA，并调整学习率 | [全参数 2/16 → 10/16](experiments/exp016-lora.md) |

偏好优化中，增大 loser 误差可能抬高相对 margin 却损伤动作；梯度保护缓解了这一现象。全参数进度训练也曾破坏 SFT 成功案例，限制更新范围后恢复到 10/16。后两项尚未超过 SFT。

<a id="早期阶段标签版本"></a>

## 实验记录

早期还尝试过成功示范内的阶段标签加权 BC，结果为 6/16；它不属于直接优化模型预测的 RL。其余信任域、执行校准与残差 actor-critic 保留在[版本索引](../../docs/rl-experiment-index.md)。

各方法的训练目标、配置、曲线和失败分析分别在 experiments 子目录。另提供[逐 seed 评测](../../data/experiments/lingbot-episodes.csv)与[动作审计](../../data/experiments/lingbot-action-audit.csv)。
