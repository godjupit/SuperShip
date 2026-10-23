# 三项组合真实输入profile

状态planned；父候选20261024-001935-kernel-weights-linear-concat，10对确认20261024-002139-kernel-paired10（基线中位333.048ms，候选310.723ms，改善6.70%，9/10更快，逐轮精度通过）。GPU0 RTX4090由本会话独占。保持三项组合、融合544，真实200张reference，cudaProfilerApi仅包围Runtime.run；初始化/预热排除，不将profiler时间作为正式成绩。
