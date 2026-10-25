# 三项组合真实输入profile

状态planned；父候选20261024-001935-kernel-weights-linear-concat，10对确认20261024-002139-kernel-paired10（基线中位333.048ms，候选310.723ms，改善6.70%，9/10更快，逐轮精度通过）。GPU0 RTX4090由本会话独占。保持三项组合、融合544，真实200张reference，cudaProfilerApi仅包围Runtime.run；初始化/预热排除，不将profiler时间作为正式成绩。

完成：源码c5056f9a6554f864b216abb52f9056d65ad9f3cd，200张/检测6323，参考AP50=0.7816，官方输出校验通过；validation/hidden本次未测。配置见config.json；命令为兼容版nsys profile --trace=cuda,nvtx,osrt --sample=none --cpuctxsw=none --cuda-graph-trace=node --capture-range=cudaProfilerApi --capture-range-end=stop -o output/20261024-002500-kernel-winner-profile/inference /home/ubuntu/.cache/supership-venv/bin/python tools/reference/profile_fastest_range.py --config experiments/20261024-002500-kernel-winner-profile/config.json --output output/20261024-002500-kernel-winner-profile/predictions.json；随后用同版nsys export --type sqlite并运行tools/reference/summarize_nsys.py。校验值与原始产物路径见metrics.json。
