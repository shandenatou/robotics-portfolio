# Rollout previews

来自 `build_tower` 的两个环境 rollout，运行 ID 为 `tower-v2-output-off`。原始 MP4 不在仓库中。

| Layout | GIF | 末帧 | 源视频 SHA-256 |
| --- | --- | --- | --- |
| 4 | [动图](tower-layout-04.gif) | [PNG](tower-layout-04.png) | `a3379971e347c56eac4a48c5b957d4fb32805ac4408635127ac229c61fe3d8a3` |
| 10 | [动图](tower-layout-10.gif) | [PNG](tower-layout-10.png) | `575ca67cd12364744edb9e2057dc7d399e69eddc6dc19cb6b73f08192ec9cd71` |

导出参数：从头到尾每 0.5 秒采样，另加末帧；480 × 360，128 色，GIF 帧延迟交替使用 120 / 130 ms（约 4 倍速），末帧停留 1 秒。播放速度只为压缩预览时长，不用于比较模型执行速度。缩放与 GIF 编码会损失画面细节。

标签与完整对照见[视频案例](../../docs/video-cases.md)。当前为本地草稿，素材公开许可待确认。
