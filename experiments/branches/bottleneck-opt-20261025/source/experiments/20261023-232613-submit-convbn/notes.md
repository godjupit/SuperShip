# 融合方案正式提交

实验 `20261023-232613-submit-convbn`；负责人Codex /root，状态completed；用户本轮明确授权正式提交一次。运行分支exp/convbn-root、完整源码 `c6d860d6b09e4566494ab2314f6482f1bb0a2a5d`，父实验 `20261023-230700-convbn-root`。本次没有改变融合实现或参数，只生成新的一次完整三轮官方日志并提交；不是从交错10次结果中挑选、拼接，也未自动重传旧成绩。

RTX4090 GPU0，北京时间2026-10-23 23:26预检空闲，预约至23:28释放。公开参考集200张，544输入、FP16、batch8、workers8、CUDA Graph、channels-last、半尺寸JPEG解码、异步输出、三层解码器、FUSE_CONV_BN=1，其余全部实际覆盖项与完整运行命令在command.json。依赖/CPU及数据权重版本与父实验一致；父实验的环境和校验和位于融合分支对应实验目录。计时器及校验器保持官方版本，READY后开始访问输入，包含全部输出fsync及进程组结束，不含初始化。

| 轮次 | 端到端秒数 | reference AP50 |
| --- | ---: | ---: |
| 1 | 0.361170067 | 0.7816 |
| 2 | 0.340258450 | 0.7812 |
| 3 | 0.327337284 | 0.7820 |

中位数 **0.340258450秒**；每轮完整200张，官方校验通过，逐轮使用score_reference.sh评分。reference基线0.7935，98%门槛0.77763，最小裕量0.00357。本次validation AP50=null（同一融合实现前阶段完整验证集AP50=0.9057），hidden AP50=null，不把先前验证值当作本轮新测值。

提交前按本机说明核对目标账号及凭证权限，凭证仅本机使用，不纳入Git。使用本机保存的原版官方submit.sh执行一次正式SUPERSHIP提交，未使用--dry；日志SHA256为 `7df2f1ffe686526ea3e95a99221ee82d36cb84c497214ea0afebc2d8695d23e5`，提交前后校验一致。官方提交指南要求完整原始三轮日志：[提交指南](https://lab.cs.tsinghua.edu.cn/scc/submit/)。

```text
Submission Time (Asia/Shanghai): 2026-10-23 23:27:49
Server Message: Submission Accepted; Performance: 0.34025845 s; OK: median runtime = 0.340258450 s (timing JSON); timing parsed only.
```

系统最近Accepted更新为本次340.3ms；只表示日志计时被接收，官方隐藏集最优仍未知。此前10次中位数329.0ms是独立本地统计，不是本次系统成绩。

原始日志、预测、评分及本机提交结果在 `/home/ubuntu/SuperShip-convbn-root/output/submissions/20261023-232613-submit-convbn/`，仅本机可用；Git保存脱敏回执、配置、命令、逐轮结果及校验和。完整三轮日志supership.out未修改。必要检查为官方输出校验、逐轮评分、三次计时/中位数一致性、日志SHA256前后一致和Git格式检查；本次无代码变化，未重复模型测试。用户仅授权一次，已经完成。
