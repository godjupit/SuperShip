# 优化日志

时间均为北京时间。完整过程与结果统一放在 **[experiments/](experiments/README.md)**；原分支继续保留自己的代码和记录。各轮原始时间和失败方案不在此重复展开。

| 时间 | 优化方案 | 结果与状态 |
| --- | --- | --- |
| 10-16 | 批量回传、锁页/异步传输、JSON批量写盘 | RTX3090验证集单次17.452→9.536秒，AP50=0.9170 |
| 10-16 | CUDA Graph、TensorRT、INT8、剪枝/蒸馏 | Graph单次9.384秒；低精度/无收益方案完整保留 |
| 10-22 | CUDA Graph组合 | RTX4090参考集三轮中位5.128→3.172秒，AP50=0.7935 |
| 10-22 | OpenCV半尺寸解码、FP16、流水线/后处理 | 历史参考集0.4766秒，validation AP50=0.9101 |
| 10-22 19:59 | 544输入、异步流水线 | 参考集0.3798秒，validation AP50=0.9054 |
| 10-23 23:07–23:57 | 99对Conv-BN融合并验证主线 | 10对中位快4.76%；主线复测0.3308秒，validation AP50=0.9057 |
| 10-24 00:04–00:29 | FP16权重、1×1转Linear、Triton特征拼接 | 历史完整三轮0.302713秒；10对快6.70%，validation AP50=0.9058 |
| 10-25 17:47–17:56 | 最快三项组合性能诊断 | 定位CPU供给、约105ms退出区间、cross-attention搬运 |
| 10-25 18:04–18:23 | 提前回收输入槽、批量结果、Triton注意力、单连接 | 10对371.4→329.0ms，快11.44%；新完整三轮316.5ms，validation AP50=0.9056；未覆盖历史约304ms |
| 10-25 | 目录归档、全分支汇集 | 已完成：9分支源码/129份原始记录集中归档，非性能实验 |
| 10-25 19:00 | Git收尾与官方规范同步 | 上游冲突已解决；批量回传兼容检查及93项测试通过；整理落到main |

以上GPU、数据划分和计时组不同，不能直接按一列排榜。RTX4090参考集不等于RTX3090或隐藏集成绩；所有hidden AP50均未测。

| 当前状态 | 定位 |
| --- | --- |
| 历史最短有效完整参考日志 | 20261024-001935-kernel-weights-linear-concat，0.302713346秒；[记录](experiments/20261024-001935-kernel-weights-linear-concat/notes.md) |
| 本轮同机推荐候选 | 20261025-180401-bottleneck-sweep；[全部实验](experiments/20261025-180401-bottleneck-sweep/notes.md)，8/10交错更快，有回退；316.5ms新日志未竞赛提交 |
| 保守高精度候选 | 640完整JPEG解码，validation AP50=0.9167；[记录](experiments/20261022-official-fast-opencv-score005/notes.md) |
| 最近Accepted信息 | 本机保留历史302.713ms回执及后续恢复记录；未在线核验当前账号。Accepted仅代表计时解析 |
| 官方隐藏集最优 | 未知 |
| 任务状态 | 20261025-190006-main-git-finish：completed；已解决上游合并与主目录整理的Git收尾 |

**常用入口**：运行`bash run.sh --worker`；基准/评分脚本在[tools/benchmark/](tools/benchmark/)；开发环境在[tools/dev/](tools/dev/)；主目录源码保持main原版本，其他优化代码见[分支快照](experiments/branches/README.md)。

[完整结果表](experiments/results/README.md) · [全部历史报告](experiments/reports/) · [各分支台账与SHA](experiments/branches/README.md) · [数据/原始产物](experiments/data/README.md)


主线已合并官方42460fba规范/评分更新，历史指标按各自固定SHA保留；后续性能比较需复测当前基线。本轮未竞赛提交。
