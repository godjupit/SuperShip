# 融合544方案：四类热点优化

状态planned，负责人Codex /root，独立分支exp/kernel-sweep-20261024，父提交121df82dd573bdfa126df985991207bc922e0351，父实验20261023-235500-main-fastest-merge。用户要求分别尝试FP16转换、concat、拷贝和卷积；先重测融合方案profile，单项独立对照三轮及精度，通过后才组合。GPU0 RTX4090，00:04预检空闲，独占诊断/计时后释放；数据/权重通过忽略的软链接引用主分支本机产物。


## 方案

- weight-half：严格加载/融合后预转Conv2d与Linear权重为FP16，保留归一化、坐标和评分FP32。
- affine-half：仅将HGNet的LearnableAffineBlock标量转FP16，减少特征升为FP32；需要重新评分，不假设数值相同。
- concat-half：Triton把特征拼接与FP16转换合并，一次写入channels-last目标；只替换紧接卷积的特征拼接，不修改解码器/结果拼接。
- encoder-layout：保留Transformer输出的channels-last布局，避免强制NCHW后再次转换。
- linear1x1：将符合条件的1x1卷积换为NHWC上的F.linear，实际检查CUDA输出和精度。

独立baseline为相同融合544配置；全部新开关默认关闭。先运行单项，发现有效项后再试组合。Triton3.2不支持此处最初尝试的指针tuple绑定/constexpr tuple索引；单元检查失败后改为显式8个指针和标量元数据接口，保留此失败原因，未把原型错误作为成功方案。

融合profile源码cb98d51，采样仅Runtime.run真实200张输入，初始化排除。完整路径output/20261024-000500-kernel-sweep/fused-profile/；kernel累计201.869ms，FP16转换9800次、26.324ms，concat单类14.044ms。原始校验值与精度在最终总结补齐。
