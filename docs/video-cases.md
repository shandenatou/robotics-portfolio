# 视频案例

[首页](../README.md) · [历史记忆](../projects/long-horizon-memory/README.md)

## 搭塔成功案例

| Layout | Early-A / 输出桥 OFF | SFT 基线 | 对应评测 |
| --- | --- | --- | --- |
| 4 | 成功，score 1，787 环境步 | 失败，score 0，1050 步 | `tower-v2-output-off` |
| 10 | 成功，score 1，785 环境步 | 失败，score 0，1050 步 | 同上 |

两段动图来自环境观测视频，并非模型预测。成功标签、score、环境步数对应评测汇总与视频清单；16 个布局的完整结果在 [memory-episodes.csv](../data/experiments/memory-episodes.csv)。

| 动图 | 末帧 | 源视频时长 |
| --- | --- | ---: |
| [Layout 4](../assets/demos/tower-layout-04.gif) | [PNG](../assets/demos/tower-layout-04.png) | 31.56 秒 |
| [Layout 10](../assets/demos/tower-layout-10.gif) | [PNG](../assets/demos/tower-layout-10.png) | 31.48 秒 |

动图从头到尾每 0.5 秒抽取一帧，缩放为 480 × 360，以约 4 倍速播放，末帧停留 1 秒。没有合成或补绘画面。[导出方式与来源哈希](../assets/demos/README.md)

本地预览可展开完整 MP4 和对应 SFT 基线。MP4 不在仓库中；动图也尚未发布，素材公开许可仍待确认。

## LingBot 的一个改善案例

`place_bread_basket`，seed 64230003：Raw SFT 失败，Exp005 成功。源视频分别为 22.5 秒和 7.5 秒，8 fps；播放时长不是执行耗时，不能据此计算提速。

两版完整评测都是 11/16，因此该片段只说明这个 seed 变好。Exp005 此条没有中止，但动作审计记录了 57 次规划失败。[32 条动作审计](../data/experiments/lingbot-action-audit.csv)

<details>
<summary>反向案例：同样保留，但不放在主展示位</summary>

seed 64230002：Raw SFT 成功，Exp005 失败。两段均无 abort 标记，Exp005 记录了 57 次规划失败。源码、原始轨迹没有完整核对前，不把规划失败次数当成已证实的失败根因。

</details>

## 公开前

8 段 MP4 保存在仓库外的本地目录；仓库草稿只包含上述两段动图及末帧。公开前仍需完成素材许可与完整内容检查。
