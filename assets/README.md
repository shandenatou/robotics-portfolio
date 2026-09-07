# 图表与视频

## 当前页面使用

- [GWP 动作优化总览](diagrams/gwp-action-guidance-method.svg)、[MC-return Q](diagrams/gwp-mc-q-method.svg)、[历史 Value＋ASAR](diagrams/gwp-history-value-method.svg)、[Action LoRA](diagrams/gwp-action-lora-method.svg)：训练与执行路径。
- [Flow-GRPO](diagrams/fastwam-flow-grpo-method.svg)、[LingBot 进度 RL](diagrams/lingbot-progress-rl-method.svg)、[分层历史](diagrams/memory-early-action-method.svg)：输入、训练对象与执行方式。
- [搭塔 rollout 动图](demos/README.md)：layout 4、10；由环境视频抽帧编码，约 4 倍速。
- [Early Action 4/8 结构](diagrams/early-action-history.svg)：按实际生效的模块重绘。
- [记忆逐布局成绩](diagrams/memory-layout-scores.svg)：由384条布局记录中的两组对照生成。
- [FastWAM训练曲线](diagrams/fastwam-training-records.svg)：40条更新、41条采样记录。
- [LingBot逐seed结果](diagrams/lingbot-seed-results.svg)：10版策略、160条记录。
- [Exp005](diagrams/lingbot-exp005-training.svg)、[Exp010](diagrams/lingbot-exp010-training.svg)、[Exp016](diagrams/lingbot-exp016-training.svg)：1500 / 1000 / 1500 条原始训练标量；Exp007 / 016 的新汇总不改写旧 160 条逐 seed 图。
- [GWP训练与checkpoint](diagrams/gwp-training-records.svg)：301条训练指标，7个eligible验证点。
- [GWP World-Value](diagrams/gwp-value-training.svg)：1500 步训练、31 次验证，选中 step 500。
- [GWP成功数与配对](diagrams/paired-results.svg)：旧汇总图，64条新取回配对记录已交叉核对。
- [阶段标签](diagrams/stage-reward.svg)、[World-Preview结构](diagrams/world-preview.svg)：按历史方案重绘。

八张数据图由 `tools/plot_experiment_records.py` 生成。SVG 为说明图和数据图，不是历史运行截图。

七张方法图由 `tools/draw_method_diagrams.py` 生成，按已核对的网络、训练目标与配置绘制；浅蓝表示训练阶段涉及的学习模块，灰色表示输入或冻结模块。评测阶段所有参数冻结。

## 旧版说明图

[六月至七月路线图](diagrams/research-roadmap.svg)、[初版总览](diagrams/research-teaser.svg)、[早期12/24层历史结构](diagrams/hierarchical-memory.svg) 保留供旧稿核对；不用于当前首页，不代表后续Early-A配置。

## 视频

8 段原始 MP4 保存在仓库外。草稿内包含两个搭塔成功案例的 GIF 和末帧，记忆页的本地预览还可展开完整 MP4 与基线链接；所有素材尚未发布，公开许可待确认。[案例说明](../docs/video-cases.md)
