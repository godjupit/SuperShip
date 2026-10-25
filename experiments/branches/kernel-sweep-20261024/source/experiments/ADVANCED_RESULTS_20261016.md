# 本次部署与压缩实验索引

每项验证集评测仅运行一次。执行成功不代表精度可采用或满足正式隐藏集要求。低精度、失败日志和权重均保留。

| 记录 | 状态 | 时间（秒） | AP50 |
| --- | --- | --- | --- |
| [cuda_graph](20261016T132410575388Z-cuda_graph/notes.md) | success | 9.384 | 0.9170 |
| [pruned_initial](20261016T132410709260Z-pruned_initial/notes.md) | success | 9.638 | 0.9112 |
| [distilled](20261016T132410829341Z-distilled/notes.md) | success | 9.634 | 0.9106 |
| [distilled_epoch1](20261016T132212694135Z-distilled_epoch1/notes.md) | success | 9.737 | 0.9087 |
| [trt_fp16_build](20261016T133945808908Z-trt_fp16_build/notes.md) | success | — | — |
| [trt_int8_build](20261016T134201051740Z-trt_int8_build/notes.md) | failed | — | — |
| [trt_int8_opt0_build](20261016T134314985327Z-trt_int8_opt0_build/notes.md) | failed | — | — |
| [trt_fp16](20261016T134226235872Z-trt_fp16/notes.md) | success | 11.958 | 0.9173 |
| [trt_int8_qdq_build](20261016T134450866542Z-trt_int8_qdq_build/notes.md) | failed | — | — |
| [trt_int8_qdq2_build](20261016T134620379594Z-trt_int8_qdq2_build/notes.md) | success | — | — |
| [trt_int8_qdq](20261016T134928683156Z-trt_int8_qdq/notes.md) | success | 12.735 | 0.8926 |
| [trt_fp16_graph](20261016T135031804981Z-trt_fp16_graph/notes.md) | failed | — | — |
| [trt_fp16_stream](20261016T135303110313Z-trt_fp16_stream/notes.md) | success | 12.484 | 0.9173 |
| [trt_fp16_graph_fixed](20261016T135325231970Z-trt_fp16_graph_fixed/notes.md) | success | 11.302 | 0.9173 |
| [trt_int8_stream](20261016T135346721277Z-trt_int8_stream/notes.md) | success | 11.105 | 0.8926 |
