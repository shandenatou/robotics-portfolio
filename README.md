# Robot learning experiments

王健昊 · [GitHub](https://github.com/shandenatou)

机器人策略后训练与历史记忆。实验基于 GigaWorldPolicy、FastWAM 和 LingBot-VA。

[GWP](#gwp) · [Flow-GRPO](#fastwam) · [进度奖励](#lingbot) · [历史记忆](#memory) · [实验记录](#records)

<a id="gwp"></a>

## GWP：价值引导控制

**任务：RoboTwin 叠三碗。基础策略：GWP-0.5，经 50-task SFT 后的 90K EMA 权重。**

在不更新基础策略的条件下，利用世界模型预测候选动作的未来，训练评价器辅助选择执行动作。

- **双 Q 保守门控：26/32 → 28/32。** 基线直接执行原策略的第一个候选；改进后从 4 个候选中选择，只有两个 Q 都认可增益才替换。
- **历史 Value 评分：23/32 → 27/32。** 这组基线是 Twin-Q＋ASAR。保持 16 候选和 ASAR 重构不变，将评分器换成读取 5 步历史、学习剩余时间进度的 Value。

两项是独立配对实验，均为固定背景下 8 个布局、每布局 4 次采样。

[项目说明](projects/gwp-rl/README.md) · [Q 门控实验](projects/gwp-rl/experiments/mc-return-q-gate.md) · [Value 实验](projects/gwp-rl/experiments/world-value-asar.md) · [SFT 基线](projects/gwp-baselines/README.md)

<a id="fastwam"></a>

## FastWAM：Flow-GRPO 后训练

**叠三碗成功率：初始策略 79/100 → 后训练 83/100。**

接通动作去噪轨迹与 RL 更新：rollout 保存完整采样轨迹，actor 按组内回报计算 advantage，完成 40 次策略更新。Randomized / Clean 各测 50 次，分别为 41→44、38→39 次成功；计数来自历史估计汇总。

[方法与结果](projects/fastwam-policy-optimization/README.md) · [训练记录](projects/fastwam-policy-optimization/experiments/flow-grpo.md)

<a id="lingbot"></a>

## LingBot：预测进度奖励

**放面包入篮：原始 Base 9/16 → 进度 RL 11/16，与另训的 SFT 对照持平。**

用三个冻结评价器的最低分作为未来预测的进度奖励，梯度经过完整 4 步去噪更新共享 Transformer；以 Base 预测作锚点，限制 latent 偏移。另做了候选偏好的梯度保护、动作约束和后层 LoRA 实验。

[方法与路线](projects/reward-action-alignment/README.md) · [进度 RL](projects/reward-action-alignment/experiments/exp005-progress-rl.md) · [偏好梯度](projects/reward-action-alignment/experiments/exp010-preference.md) · [LoRA](projects/reward-action-alignment/experiments/exp016-lora.md)

<a id="memory"></a>

## GWP：历史记忆

**基础策略：35-task SFT，step 50K；任务环境：RoboDojo。**

当前观察查询分层视觉历史，读出 8 个 memory tokens，通过门控残差注入 ActionExpert 第 4、8 层。训练历史模块，冻结策略主干。

| 任务 | SFT 成功数 | Early-A 成功数 | 阶段均分：SFT → Early-A |
| --- | ---: | ---: | --- |
| 倒瓶入桶 | 10/16 | **12/16** | 0.7406 → **0.8313** |
| 搭塔 | 0/16 | **2/16** | 0.0500 → **0.2688** |

两项成功率均增加 12.5 个百分点。搭塔使用输出桥关闭版本；具体选点与消融见记录。

[方法与视频](projects/long-horizon-memory/README.md) · [训练与消融](projects/long-horizon-memory/experiments/early-action-history.md)

<a id="records"></a>

## 实验记录

[全部实验](docs/rl-experiment-index.md) · [CSV / 配置](data/experiments/README.md) · [代码来源与公开范围](docs/reproduction-status.md)

各项目的 `experiments/` 保存基线定义、训练目标、配置、评测记录及简要失败分析。本仓库包含项目文档与整理后的实验数据，未包含完整训练实现。
