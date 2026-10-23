# Conv-BN 权重融合尝试

实验 `20261023-230700-convbn-root`；负责人 Codex /root；状态 completed；北京时间2026-10-23 23:14更新。分支 `exp/convbn-root`，父实验 `20261022-195852-further-confirm-size544`，父提交 `4971fb72cf67f6295da02bd25b9f204c766a95e3`。性能与精度实验使用的融合实现完整提交为 `84fd5fe09124a8b8ee28f7e6cc1d9a60f6e70165`。后续仅补充验证脚本、测试及记录，运行时实现未变。

结论：**融合与精度检查通过，但端到端加速未稳定复现；保留为可选开关，不晋级默认最快候选。** 原544最快候选、640高精度保守候选和历史Accepted提交保持不变；官方隐藏集最优未知。本次未进行竞赛提交。

## 修改及覆盖

增加 `FUSE_CONV_BN=1`，严格加载官方权重并切换eval后、channels-last转换及合成预热/CUDA Graph捕获前，使用PyTorch的 `fuse_conv_bn_eval` 折叠权重。只处理已核实forward连接的HGNet ConvBNAct、编码器ConvNormLayer及Sequential内直接相邻的Conv2d/BN，保留padding、激活、分支求和、三层解码器和原checkpoint。支持普通/冻结BN，拒绝训练态或缺少运行统计的BN，不根据任意模块注册顺序推断连接。默认关闭。

实际checkpoint共99个BatchNorm2d，融合99对，剩余0个；名单及合成输入误差见coverage.json。整模型MODEL_DEPLOY保持0，以隔离本次假设。

## 同协议结果

GPU0 RTX4090，23:07预检空闲，独占到23:14释放；期间按顺序运行，不并发性能任务，结束预检仍无GPU进程。AMD EPYC7402、10个可见逻辑核；依赖见environment.json。沿用同一公开数据与官方权重，校验和见metrics.json。未修改计时器或输出校验器，READY后才访问评测输入，全部输出fsync及进程组退出计时，初始化不计时。

固定544输入、batch8、workers8、prefetch3、FP16 autocast、channels-last、CUDA Graph、OpenCV半尺寸JPEG解码、cvtcolor写锁页缓冲、异步回传、score0.05、cuDNN benchmark。全部显式配置在config.json，实际每次配置/命令/cwd保存在commands.json。基线使用父版本原worktree的未修改worker；融合组使用本实验worker。

| 组别 | 三轮端到端时间（秒） | 中位数（秒） | 每轮reference AP50 |
| --- | --- | --- | --- |
| 基线，首组 | 0.342843022 / 0.343989090 / 0.376995317 | 0.343989090 | 0.7814 / 0.7815 / 0.7814 |
| 融合，首组 | 0.327972431 / 0.335364142 / 0.332367181 | 0.332367181 | 0.7814 / 0.7813 / 0.7817 |
| 基线，复测 | 0.350231934 / 0.380820684 / 0.345110039 | 0.350231934 | 0.7816 / 0.7813 / 0.7819 |
| 融合，复测 | 0.367203500 / 0.324805539 / 0.365588829 | 0.365588829 | 0.7813 / 0.7813 / 0.7814 |

首组缩短3.38%，复测反而增加4.38%，且分布重叠。全部六轮合并中位数基线0.347670987秒、融合0.333865662秒（缩短3.97%），但不能用这个汇总掩盖复测方向相反，故不宣称稳定提速。不挑选最快一轮或只保留首组。cuDNN算法搜索、GPU时钟及系统负载可能影响结果，本次未单独归因。

参考集200张全部通过官方校验与逐轮评分。基线reference AP50=0.7935，98%门槛0.77763；融合最低0.7813，保留98.463%，裕量0.00367。

完整验证集1,030张（含尾批6张），融合AP50=0.9057；同集原始基线0.9170，98%门槛0.89866，保留98.768%，裕量0.00704。历史未融合544候选validation AP50=0.9054，不把0.0003差异解读为稳定精度提升；本次未重新测量未融合validation AP50。融合验证仅一次，耗时1.478530406秒，不与200张参考集时间混比。hidden AP50=null。

## 正确性与失败记录

- 7项基础测试覆盖非平凡BN统计、bias、分组卷积、padding、普通/冻结/非仿射BN、幂等性及拒绝不安全连接。初版首次折叠数值检查通过，但重复调用因新Identity默认training=True失败，改为eval态后7项通过；失败未用于性能结果。
- CUDA集成测试比较融合/未融合图路径，在11张合成图片、batch2、prefetch3、异步环形复用下覆盖完整输入及尾批；框一致、分数容差1e-5。
- 初版整模型合成FP32逐元素比较在默认TF32设置下失败（最大框差约0.98），日志及当时inspect脚本保留在output中，不作为正确性通过证据。随后明确关闭TF32验证FP32折叠，编码器三尺度特征最大绝对误差约1.16e-5，完整输出框最大误差约1.02e-4、logit约1.97e-4。合成输入FP16输出仍有明显差异，模型含离散top-k查询选择，不能要求预测列表逐元素等价，也不据此跳过真实数据精度检查；最终以所有参考集轮次及完整验证集AP50检查为准。
- 全套测试：`/home/ubuntu/.cache/supership-venv/bin/python -m pytest -q tests`，56 passed、1 skipped（可选TensorRT引擎缺失）；git diff --check通过。GPU占比没有重新采集，不能把旧profile中的15% BN时间直接当作本次端到端收益。

## 复现

在本分支独立worktree准备相同校验和的数据和权重后运行（输出目录必须不存在）：

```bash
PY=/home/ubuntu/.cache/supership-venv/bin/python
$PY experiments/20261023-230700-convbn-root/run.py --fuse 0 --output output/convbn-reproduce-control
$PY experiments/20261023-230700-convbn-root/run.py --fuse 1 --output output/convbn-reproduce-fused
$PY experiments/20261023-230700-convbn-root/run.py --fuse 1 --split val --runs 1 --output output/convbn-reproduce-validation
$PY experiments/20261023-230700-convbn-root/inspect_fusion.py --output output/convbn-reproduce-coverage.json
```

run.py使用未修改的官方计时器与校验器，默认三轮，每轮独立进程并评分；实际对照命令另用 `--root /home/ubuntu/SuperShip-optimize` 运行父版本。检查脚本只使用合成输入，不访问评测数据；最终脚本支持指定新输出路径并拒绝覆盖已有文件。实际检查时尚使用固定coverage.json路径，随后仅调整了报告路径保护。

初始化及GPU测试时工作目录为 `/tmp/SuperShip-convbn-root`；结束后完整worktree迁移到 `/home/ubuntu/SuperShip-convbn-root`，原始命令/日志保留执行时路径。全部原始预测、计时/评分/检查日志在该worktree的 `output/20261023-230700-convbn-root/`；只在本机可用，不随Git推送。Git保存全部逐轮指标、配置、命令、融合名单与SHA256索引。后续不覆盖旧目录。

下一步若继续此方向，应先区分GPU计算与退出/主机波动，再决定是否做更多交错计时；当前默认候选保持未融合544方案。

性能实验后补充的数值检查脚本和集成测试差异保存为source.patch，SHA256 `0bdb4a34b8d697203ba7f847f8ec7a00852c138cd18722fcdc06a0322bb8deb0`；推理运行时始终对应84fd5fe完整提交。
