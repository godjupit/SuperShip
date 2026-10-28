# 优化版本索引

## 20261028-185816-cpu-affinity

- Owner Codex/root；status planned（文件阶段）；branch `exp/cpu-affinity-20261028`，worktree `/data/run01/sczf193/SuperShip-affinity-20261028`，base main `2a3206d`；父诊断20261028-183651-profile-supply，跟进cpu-supply的RGB未确认收益。GPU g0030/RTX4090、Slurm1353441固定8核，仅在cpu-supply诊断结束交接后启动。
- 新独立假设：同一8核内主线程/CUDA等待与解码/JSON线程迁移或争用导致慢轮。增加默认关闭CPU_AFFINITY=split/pin：保留主线程1核、JSON1核、解码6核；split允许6解码线程在6核内迁移，pin每线程固定一核。不增加资源，不改变输入/模型/精度/输出，不组合RGB或blocking新开关。
- 先验证实际线程mask、无越过初始调度cpuset、GPU异步ring/reuse/尾批/graph，再baseline-start、split、pin、baseline-end各完整三轮及逐轮精度/byte检查。仅有希望的候选做独立16组AB/BA，预设至少13/16胜且同组中位改善，之后新完整三轮才可晋级/提交；不按单轮或插桩提速选版。
- 所有原始产物output/20261028-185816-cpu-affinity/仅本机；配置沿用eightcore-thread6，reference门槛0.777042、validation/hidden=null，Accepted0.256022902秒保护。前两CPU单项失败保留，不将其开关默认带入本轮。Git同步认证已知失败，本地分支与历史保留。

## 20261028-184009-cpu-supply

- Owner Codex/root；status running（18:43开始GPU检查与筛查）；branch `exp/cpu-supply-20261028`，worktree `/data/run01/sczf193/SuperShip-cpu-supply-20261028`，base main `c03c9bf`（完整SHA由Git和plan记录），父诊断20261028-183651-profile-supply；g0030/RTX4090、Slurm1353441、固定8核。必须等诊断全部结束再运行，无GPU并行计时。main仍为最快已验证版本，GitHub认证阻塞不改写历史。
- 新单项A：OPENCV_RGB=1，直接按RGB解码+resize到锁页输入，去掉BGR转RGB与中间resize缓冲。OpenCV4.11原生支持RGB标志，与JPEG减采样位分别保留，禁止同时GPU_BGR；先检查不同图像格式/奇数尺寸/全部减采样与已有RGB像素完全一致。
- 新单项B：BLOCKING_EVENTS=1，使H2D复用与D2H输出事件的CPU synchronize使用休眠等待；保留全部GPU依赖和输出完整性，避免默认忙等抢占CPU。与A独立。先GPU ring/reuse/tail/graph测试，再baseline-start、RGB、blocking、明确父组合RGB+blocking、baseline-end各完整三轮及逐轮精度/字节检查；基于诊断的CPU单项，不重复上轮SDPA/deploy组合。
- 全配置沿用eightcore-thread6。若有收益候选，预登记独立16组AB/BA（合计至少13/16胜、同组中位改善）并新完整三轮后才晋级/提交；失败/无收益照实保留，不按微测或单轮晋级。原始产物output/20261028-184009-cpu-supply/，仅本机；reference门槛0.777042，validation/hidden未测，Accepted0.256022902秒受保护。
- 源码初始ec089da，测试修正2860925（完整SHA见plan）。首次6失败/114通过均为原有路径对奇数PNG减采样向下取整与metadata向上取整的合同不匹配；失败发生在baseline而非新RGB路径，保留checks-odd-png-baseline-failed.log。PNG比较采用能被全部减采样整除的尺寸，奇数尺寸JPEG/灰度/CMYK均保留；不改生产尺寸合法性策略。随后120项检查全部通过（16.69秒），开始15完整worker筛查；全部阻塞事件/复用/尾批/CUDA Graph组合通过。
- 15轮筛查全部完整200张/6102检测、reference AP50均0.7809、预测与原版本byte一致；起止基线中位0.261959731/0.269046773秒，RGB0.254450720、blocking0.261159286、RGB+blocking0.299882713。候选RGB独立16组AB/BA确认开始，沿用预登记13/16胜和同组中位收益门槛，全部轮次保留。

## 20261028-183651-profile-supply

- Owner Codex/root；status completed；2026-10-28 18:36–18:41 CST；branch main，source `2174a95`（完整SHA在plan中）；GPU g0030/RTX4090，Slurm1353441，固定8核。18:36确认显存1MiB、利用率0、无计算进程；所有计算/测试/分析仅在该调度分配执行。当前main仍为最快已验证eightcore-thread6；用户要求瓶颈分析后按新思路优化。
- 当前6线程配置与旧10线程诊断不同，建立新组：原始worker完整三轮；轻量CPU阶段三轮；低开销CUDA Event三轮；一次PyTorch CPU/CUDA trace；一次strace退出诊断（工具可用才执行）。所有真实输入访问在READY后，输入/预测/完整日志本地NVMe，全部输出核对格式/完整200张/精度及历史字节。插桩结果不作为成绩，不修改评分器、worker或默认配置。
- 原始产物 `output/20261028-183651-profile-supply/`（仅本机），独占GPU18:36开始。基于诊断提出新单项假设、独立分支登记后再实验，不重复上一轮未确认的GPU组合。最近Accepted0.256022902秒保护，validation/hidden未测，官方隐藏集最优未知。Git推送已知认证失效，完成记录后仍从登录节点同步。
- 11个完整200张worker全部6102检测、reference AP50=0.7809、预测byte一致。正式三轮0.260369892/0.325555410/0.265296650秒，中位0.265296650。CPU阶段：JPEG解码802–806ms累计线程CPU、resize116–118ms、主线程Future等待141–159ms；输出write/fsync/close约0.94–2.03ms。CPU累计不能与端到端或重叠GPU时间相加。
- CUDA Event图/拷贝包络并集129–131ms、包络间空档21–31ms，核心后退出76–80ms。PyTorch trace19050kernels/13561个<5us、GPU活动并集130.128ms/跨度158.706ms；独立strace主进程exit_group→退出75.654ms，支持OS退出资源回收明显但未唯一定位NVIDIA函数。nsys/perf缺失。插桩非成绩。
- [完整诊断与复现](docs/performance-g0030-20261028.md)。旧10线程大尺寸准备停顿未在当前6线程复现（约1.5–1.7ms），不再据旧数据归因。简单empty_cache/malloc_trim/device reset历史已否定，本轮未重复。18:41 GPU交给cpu-supply隔离实验；无竞赛提交，候选与Accepted不变。

## 20261028-175402-gpu-confirm

- Owner Codex/root；status completed；2026-10-28 17:54–18:23 CST；branch `exp/gpu-confirm-node-20261028`，worktree `/data/run01/sczf193/SuperShip-confirm-20261028`，base `712894c`，父实验 gpu-factorial 与 gpu-sdpa；原有未提交改动保留。当前 main 仍为最快完成独立确认的候选；推送尝试因 GitHub 认证失效失败，保留本地历史。
- GPU g0030 / RTX4090，调度分配1353441，固定8核；17:53检查显存1MiB、利用率0、无计算进程，仅用户交互bash。所有项目计算/测试仅在该分配执行，正式计时独占GPU，数据/预测/完整日志位于节点唯一/tmp目录后同步output。
- 新比较组（节点变化）：先完整三轮 baseline、deploy、deploy+SDPA decoder、deploy+SDPA all+MHA half、deploy batch16/workers8、baseline-end；所有配置基于eightcore-thread6。仅在完整参考AP50>=0.777042、格式/完整覆盖/尾批检查通过后，对最快候选与基线进行8组交替AB/BA确认，波动重叠则不晋级。SDPA实现来自4fa0cc2完整提交；部署/SDPA组合明确沿用父实验，不重复已否定512输入。
- 用户授权经过验证的新优成绩直接提交；先核对官方榜单当前账号计时，使用同一份原始三轮日志先dry run再计分。最近历史Accepted0.256022902秒受保护，17:53官方榜单核对ruc26**仍为0.256022902秒，榜上最快0.249195662秒；validation/hidden未测，官方隐藏集最优未知。原始结果 `output/20261028-175402-gpu-confirm/`，仅本机可用。

- 驱动部署失败保留：首次worktree在登录节点/tmp，计算节点不可见，未启动任何模型；跨文件系统git worktree move失败，随后在共享路径新建隔离分支。原/tmp worktree保留。实际源码2b1505c（与父SDPA实现一致），driver-v3.log为有效运行，前两份失败日志保留。
- 测试驱动初次误将生产INPUT_SIZE544等preset注入合成模型测试，108通过/12失败（SyntheticModel无encoder），失败日志checks-preset-failed.log保留；清理测试env后120项全部通过（187.23秒），未改生产源码或测试断言。driver-v4.log为有效筛查，18个完整worker预登记开始。
- 六组/18完整参考worker全部完成、逐轮格式与精度通过；baseline-start中位0.283797543、baseline-end0.257816384，明显漂移。deploy0.284665107、deploy-decoder0.254883489、deploy-all-half0.256723748、deploy-b16-w8为0.253545784秒，AP50分别0.7820/0.7821/0.7807/0.7817。选择deploy-b16-w8进行预登记8组AB/BA独立确认；不按筛查直接晋级或提交。
- 18:11追加预登记：batch16前两对均未获益；仍完成全部8对，不提前截断。如果该候选收益不成立，独立复测deploy-decoder（仅MODEL_DEPLOY1 + SELF_ATTN_SDPA=decoder，batch8/workers6），也做完整8组AB/BA，不将两候选轮次混合；只有稳定收益且新三轮优于Accepted才晋级/提交。
- 第一轮8对：batch16中位0.2596558715→0.258028366秒，仅5/8胜、改善0.6268%，不采用。decoder SDPA中位0.2623495235→0.2582724395秒、6/8胜、改善1.5541%，属于小幅/重叠。18:18预登记另8对完全相同decoder比较，合计至少13/16胜（双侧符号检验p<=0.0213）且中位改善才继续候选新完整三轮；否则本轮不晋级/不提交，不无限重复筛选。
- 最终：追加decoder8对仅3/8胜；合计16对9胜，基线中位0.2620592415→候选0.2600364525秒，改善0.7719%，双侧符号检验p=0.803619，不满足预登记13/16门槛。batch16与decoder两候选均不晋级、不竞赛上传；保留原main eightcore-thread6、本地最快已确认候选及Accepted0.256022902秒，保守640候选不变。validation/hidden AP50=null，官方隐藏集最优未知。
- 完成6组/18筛查轮＋24对/48确认轮＝66完整200张worker；逐轮输出格式、参考精度及字节复核通过，候选reference AP50范围0.7807–0.7821；120项GPU节点检查通过（首次驱动污染失败另存）。完整运行日志54份，环境/源码/数据/权重manifest、全部驱动/实际命令/配置/预测/日志SHA256保存在output下，跨机器产物缺失须重新准备。18:22 GPU显存1MiB、无计算进程，本会话计算结束，保留用户1353441分配与交互shell。
- 复现与全部逐轮表：[experiments/20261028-175402-gpu-confirm/notes.md](experiments/20261028-175402-gpu-confirm/notes.md)。没有改main运行实现；实验源码2b1505c完整SHA见报告，独立分支保留。下一步优先分析更大输入规模下CPU供给和退出开销，当前GPU微测提速未稳定转化为200张端到端收益，不继续重复筛选本轮候选。
- Git同步：登录节点已尝试push，GitHub认证因失效的vscode-git套接字失败；文档提交本地保留，最终推送状态见交接。竞赛未提交，无新回执。

## 20261027-131100-gpu-sdpa

- Owner Codex/root；status planned（文件编辑阶段，不占GPU）；branch `exp/gpu-sdpa-20261027`，独立worktree `/data/run01/sczf193/SuperShip-sdpa-20261027`，基于当前main（推理实现与981d8dc相同，完整base由Git记录）。GPU仍由gpu-factorial实验独占，所有运行/测试必须等交接，不在登录节点执行。
- 新单项假设：编码器/解码器MultiheadAttention默认need_weights=True，但调用者丢弃权重。新增默认关闭的SELF_ATTN_SDPA开关，仅在eval且禁用梯度时传need_weights=False，允许PyTorch选择SDPA，保留训练和梯度路径。与deformable cross-attention的Triton实现独立，不改权重/结构/输入，不从参考图像预计算任何内容。
- 先验证训练/梯度guard、FP16/FP32数值、mask和CUDA Graph更新，再固定8核/原始参数测完整参考3轮、GPU时间线及精度；必要时与factorial已通过的GPU组合做明确父实验组合。只有完整合法性/精度及8组交替收益确认后晋级，失败保留，近期Accepted0.256022902秒受保护。

## 20261027-125042-gpu-factorial

- Owner Codex/root；status running；base main `981d8dc401318daaf1bb2a2f2ec04f71374abd27`，登记后base `2676385a3232ee090cbca0f5b4737fab4ddd6d31`；当前最快8核配置已在main，已从登录节点尝试推送但认证仍失败；不因此改写历史。branch `exp/gpu-factorial-20261027`，独立worktree `/data/run01/sczf193/SuperShip-gpu-factorial-20261027`。
- 用户明确允许回看旧优化、非贪心重新组合。GPU g0005/RTX4090，分配1351172，固定8核/6解码线程，12:50CST检查GPU无其他计算进程。保持200参考集、模型权重、输入544、精度判据和完整worker计时协议；validation/hidden未测。最近Accepted0.256022902秒受保护。
- 非贪心GPU随机输入筛查：部署融合2×1x1 Conv/Linear2×ReLU-affine三态（未融合/保留FP32输出/FP16输出）×原生cat/Tritonpack2×cuDNN调优2，共48组合；另独立回退权重FP32、未融合BN、原生注意力、原生GPU组合，以及融合归一化、融合后处理、GPU BGR、encoder layout等对照。所有组合先登记，随机顺序、重复基线，三次CUDA Event计时；随机输入完全不访问评测数据，不视作正式E2E或精度证据。
- 根据隔离GPU结果登记少量候选后完整独立三轮、逐轮评分和完整覆盖/尾批检查，再对有希望的组合进行8组交替确认；不要求候选保留现在的全部旧开关，允许按更早组合分支。所有失败、无收益及数值改变保留，不将合成微测直接晋级或用于计分提交。GPU计算/测试只在计算节点，日志及评测输入输出全本地NVMe。
- 设计修正：首次混合cuDNN benchmark开关的单进程预试已中断并保留，存在算法缓存跨设置沿用的风险，不用于选版或声称收益。正式微测将benchmark0与1分到全新独立进程，内部做全部联合组合/重复控制，避免将缓存状态误认为某个开关收益；不修改生产代码。
- 62个正式合成微测已完成（48联合+8回退/融合对照+6控制），全部有限输出。当前组合GPU约4.50ms/batch，部署融合组合约4.37ms；退回原生GPU组合约8.11ms、去掉BN融合约5.66ms、原生attention约5.64ms，旧优化并非全部多余。仅GPU结果，不据此晋级。cuDNN调优增益很小，保留独立端到端检查。
- 下一阶段预登记15组完整三轮：部署0/1×batch8/16×workers6/8共8组合；部署1/b8/w6增加fused-normalize、GPU-BGR两组；部署1/b16/w6与w8各增加GPU-BGR两组；部署1/b8/w6/cudnn1一组、原生GPU组合一组、结束控制一组。其余参数冻结。随机顺序中保留起止控制，逐轮评分和完整覆盖；不要求继续沿用刚晋级的6线程或batch8，不混同GPU微测与E2E收益。更小输入512已有validation失败证据，本轮不重复该已否定方向。TensorRT/ONNX当前未安装，先验证现有实现组合。

## 20261027-120927-supply-eightcore

- Owner Codex/root；status completed；main parent `9e6d3c6283ab64ef5e9f4943dfede4f47144d815`，实验base `2835ecca867fa49cf349581039bf24102e164425`，晋级启动配置 `fde3318233ea55776ab15302a3521d20b88e146f`；branch `exp/supply-eightcore-20261027`，独立worktree `/data/run01/sczf193/SuperShip-eightcore-20261027`。计算运行12:09–12:34CST完成，GPU空闲后释放本会话占用，保留用户1351172分配。登录节点推送因Git认证失效失败，成果保留在本地提交。
- 用户授权优化当前仓库；GPU g0005/RTX4090，分配1351172，8核固定，12:09CST检查GPU无其他计算进程。只在该计算节点进行计算、测试与评分；输入/预测/全部日志本地NVMe，结束同步output。
- 首个假设：8核下主线程供给/小张量准备与10个解码线程存在调度争用。分别登记独立配置baseline10-start、PINNED_SIZES=1、workers8、workers6、workers4、baseline10-end各3完整轮；不改模型、精度、输入大小、JPEG模式及输出。旧机器/共享日志结果不能替代本比较组证据；所有结果保留。筛查后只对有希望的单项或明确父实验组合做8组交替对照；输出byte一致、reference门槛及尾批检查后方可晋级。validation/hidden未测，无竞赛提交授权扩展。
- 初筛workers6三轮0.242042113 / 0.257647905 / 0.256022902秒，参考AP50均0.7809、预测byte一致。登记8组baseline10/workers6交替AB/BA对照，待六组筛查全部结束后启动，不与其他GPU任务重叠；不因为单次最快或三轮筛查而提前晋级。锁页尺寸无收益，8线程收益接近噪声，4线程明显变慢，完整结果保留。
- 完成6组/18轮筛查、8组/16轮独立交替确认和晋级默认入口3轮，共37个完整200张worker，全部6102检测、reference AP50=0.7809、预测SHA256 `4185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c`。54项初始及74项最终启动器/覆盖优先级/异步ring/尾批/像素检查通过。validation/hidden未测，官方隐藏集最优未知。
- 8组对照baseline10中位0.3093000845秒，workers6中位0.261835146秒，快15.3459%，8/8胜，双侧符号检验p=0.0078125。默认入口自动选6复测三轮0.258169335 / 0.261901917 / 0.246521152秒，中位0.258169335；模型、GPU推理、计时器、精度及输出均未改变。仅Slurm每任务8核时默认6线程，其他环境保留10，显式NUM_WORKERS始终优先；保留完整历史10线程参数。
- 已核对官方现有0.258409792秒后，经dry run于2026-10-27 12:38:08CST正式提交本轮初筛完整三轮原始日志，**Accepted0.256022902秒**（timing parsed only）；日志SHA256 `18fc4ebea72f851c4f972d0cac4905dc785f33b44a2a589fbec6487e2f2c1d12`，来源base2835ecc+NUM_WORKERS6，与晋级有效配置一致。未拼接单轮、未重传旧Accepted。脱敏回执：[docs/receipts/20261027-120927-supply-eightcore.txt](docs/receipts/20261027-120927-supply-eightcore.txt)。本地凭证及原始认证回执只在Git忽略的.local目录。
- 原始命令、所有配置覆盖、完整逐轮结果、环境/数据/权重校验和、源码patch及失败/无收益结果保存在本机 `output/20261027-120927-supply-eightcore/`；跨机器需重新准备公开数据权重。源码patch SHA256 `7aa942b3a03685b920e5d391b15103e2486aa3c3c8930bd601b3213f588591a2`；完整报告及复现：[docs/optimization-eightcore-20261027.md](docs/optimization-eightcore-20261027.md)。本比较组推荐6线程；保守640完整JPEG候选保留。

## 20261027-115247-profile-g0005

- Owner Codex/root；main source `e41488e23da4949afbe3a192b1622b8e6689f94a`；status completed；GPU g0005/RTX4090分配1351172，8核固定，11:52–12:00CST；GPU初始无计算进程、显存1MiB、利用率0，结束后显存1MiB/利用率0，本会话任务结束，用户分配保留。
- 用户请求当前机器瓶颈诊断；默认thread100-light，输入/预测/完整日志均节点NVMe。先不插桩正式三轮及逐轮评分，再独立轻量阶段/CPU/IO/退出诊断三轮，单独PyTorch CPU/CUDA profiler时间线；无nsys安装则记录工具限制，不修改计时器、模型或worker源码。插桩数据不作正式速度排名，不做竞赛提交，不调整CPU配额。全部产物 `output/20261027-115247-profile-g0005/`，计算只在GPU节点。
- 11:57追加验证登记：PyTorch profiler已获得19050个kernel事件，但工具会扰动CPU调度；增加三轮仅CUDA Event的graph/H2D/D2H区间诊断，复核正常速度附近的GPU空档。标记图执行包络包含图内小间隙，不能当作精确kernel活跃率；全部结果保留。
- 正式完整三轮 `0.285036207 / 0.293397743 / 0.326934422` 秒，中位 **0.293397743**；阶段诊断三轮核心219.948/255.780/253.151ms、剩余退出区间63.296/66.404/67.938ms。JPEG读取/解码累计810–822ms线程CPU、占进程CPU约76–77%；输入Future等待67–109ms（与GPU重叠），输出write/fsync/close2.2–3.0ms，物理read_bytes增量0。
- PyTorch trace的kernel/copy/memset并集128.891ms，19050kernels、13731个<5us；profiler下的129.522ms空档不可直接视作正常运行值。独立低开销Event三轮graph/copy包络间空档61.372/48.644/28.284ms，核心241.291/231.451/186.414ms，核心后至退出72.248/73.394/68.359ms；含marker影响，不替代正式计时。优先级：CPU解码/供给与主线程调度，其次退出，再GPU pack/转换/短kernel；没有提高CPU配额或修改默认参数。
- 全10个正式/诊断worker各完整处理200张、6102检测，逐轮reference AP50=0.7809，全部预测SHA256仍为 `4185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c`。validation/hidden未测、无竞赛提交，候选推荐不变。完整报告及复现说明：[docs/performance-g0005-20261027.md](docs/performance-g0005-20261027.md)；两份可复用诊断worker位于tools/reference/，实际完整输入/输出已验证，GPU节点py_compile通过。原始trace/日志/预测/命令及source-SHA256SUMS仅上述本机output目录可用。
- 新增诊断脚本的可还原patch存于该output目录source.patch，SHA256 `6e7dcfe12a18505a0d877ef8fa050a6e02dce062653915be5961c3f57a389766`；正式worker源码无改动。Git仅提交本次报告、台账和必要诊断源码，原有未跟踪文件不包含在提交中。

## 20261027-114732-node-g0005

- Owner Codex/root；main source `7c8a161e3989b5ab341069fa7d3734975ad2145d`；status completed；用户要求切到五小时作业1351172，g0005/RTX4090/8核，分配结束15:57:33CST；11:47–11:48运行前GPU无计算进程，显存1MiB/利用率0。
- 与g0067全本地运行对照：精确thread100-light JSON、固定8核、200张参考集三轮、输入/预测/完整日志均位于节点/tmp NVMe，结束后同步结果到 `output/20261027-114732-node-g0005/`。不增加CPU，不改实现，不进行竞赛提交。旧节点分配保留，不终止用户交互shell。
- 命令：`srun --jobid=1351172 --overlap --ntasks=1 --cpus-per-task=8 --chdir=/data/run01/sczf193/SuperShip-main bash output/20261027-114732-node-g0005/run.sh`；完整执行脚本保存在上述本机输出目录，部署副本 `/tmp/supership-20261027-114732-node-g0005/` 留在g0005。环境为EPYC7502、Python3.11.11、torch2.5.1+cu124、OpenCV4.11.0，准确驱动/CPU/配置与数据权重校验和见environment.log；只有台账/运行说明未提交改动，无运行源码改动。
- 全三轮 `0.305249523 / 0.299772560 / 0.313619927` 秒，中位 **0.305249523**；每轮完整200张、6102检测、官方格式检查及评分通过，reference AP50均0.7809。输出SHA256与历史及g0067均为 `4185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c`；validation/hidden未测。新节点本轮比g0067的0.261382914秒稍慢，属于节点环境对照，不据三轮筛查宣称稳定差异或调整main候选。后续按用户要求使用五小时g0005分配，GPU任务已完成，分配保留。

## 20261027-114037-storage-diagnosis

- Owner Codex/root；main `7c8a161e3989b5ab341069fa7d3734975ad2145d`；status completed；GPU g0067/RTX4090，分配1351209，11:40–11:47CST，启动前GPU空闲。仅运行诊断，不改实现、不晋级候选、不竞赛提交；本会话工作已结束，用户分配保留。
- 核对最近thread100-light JSON与默认配置，排除环境覆盖；单一主要假设：共享JuiceFS输入/输出造成约1.6秒延迟，比较完全相同配置下共享存储三轮和本地NVMe输入/输出三轮，另立存储比较组，分别评分。节点为EPYC7502、分配8核；完整数据准备作为显式部署步骤，worker仍须READY后访问输入。原始结果 `output/20261027-114037-storage-diagnosis/`，本地数据与结果保留于该节点唯一/tmp目录，不缓存评测答案。
- 11:43追加诊断登记：用户明确CPU固定8核，禁止增加分配。保持默认配置分别做共享/本地一次独立插桩诊断，将核心处理与退出区间分开（插桩结果不作正式性能比较）；确认剩余差距来源。随后本地盘 workers8/6各完整三轮仅检查固定8核下线程竞争，保留默认10线程对照；未确认收益前不改默认配置。
- 11:46追加单一存储假设：上面的本地输入/输出对照仍将worker stderr日志写到共享盘，完成阶段的stderr flush包含在官方计时内。新增最近默认10线程配置、本地输入/输出/日志完整三轮，结束后再拷回共享目录；不屏蔽日志、不改计时器、不省略fsync，保持固定8核。
- 已完成：默认10线程、共享输入/预测/日志三轮 `0.591817180 / 0.460150161 / 0.955263980` 秒，中位0.591817180；本地输入/预测、共享日志三轮 `0.355758293 / 0.485003780 / 0.459530471` 秒，中位0.459530471；**本地输入/预测/完整日志**三轮 `0.260419176 / 0.282751773 / 0.261382914` 秒，中位 **0.261382914**，与历史约0.258秒接近。全部固定8核，不是增加CPU的收益；最近JSON所有参数不变。顺序筛查未做配对显著性检验，不宣称存储收益的精确因果百分比。
- 仅插桩诊断（非正式对比）：共享核心0.345783秒/端到端0.928055秒；本地核心0.196726秒/端到端0.418281秒，两个日志仍在共享盘，剩余区间含末尾stderr刷新和进程退出，不能全归因内核退出。最终全本地日志实验支持共享日志刷新是关键额外开销；首次1.612565秒还有共享存储冷热/波动，未逐项量化。
- 固定8核线程筛查：workers8三轮0.430404523 / 0.371507274 / 0.422572330，中位0.422572330；workers6三轮0.365634567 / 0.550403962 / 0.352342635，中位0.365634567（均本地输入/预测、共享日志）。波动较大，不更改默认10线程配置，不据此推荐新的最快参数。
- 全部15个正式筛查worker完整处理200张/每轮6102检测，逐轮reference AP50均0.7809；预测SHA256均 `4185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c`，与历史最佳输出一致；validation/hidden未测。完整命令脚本、环境、逐轮日志、评分、预测与校验和保留在本机上述output目录；节点/tmp副本保留，不代表跨机可获得。可复现的全本地命令已写入 docs/commands.md；未修改模型/worker/评分器或默认配置。

## 20261027-113500-runtime-reference

- Owner Codex /root；branch main；source `a39ea8e81f1ad0bcd75072f1101bc5ca1fc1e603`；status completed；2026-10-27 11:35–11:39 CST；GPU 分配 `1351209`，节点 g0067，RTX4090。启动前调度状态 RUNNING，GPU 显存占用0、利用率0，无其他计算进程；结束后GPU显存占用0，无本会话任务残留，保留用户的现有调度分配。
- 用户授权运行项目；复用现有有效分配，不在登录节点执行计算。不修改推理实现，使用 configs/fastest.env 默认参数；参考集完整三轮和逐轮评分，独立目录 `output/20261027-113500-runtime-reference/`。新环境比较组，仅验证运行，不直接与历史速度排名，无竞赛提交。
- 环境：8个分配CPU，Python3.11.11、torch2.5.1+cu124、OpenCV4.11.0、驱动580.82.07；依赖和CPU资源与历史环境不同，存储冷热状态未控制，不跨组比较。未改运行源码；本次未提交改动仅为台账。所有配置来自 configs/fastest.env，无性能参数覆盖。
- 实际运行：`srun --jobid=1351209 --overlap --ntasks=1 --cpus-per-task=8 --chdir=/data/run01/sczf193/SuperShip-main bash -c 'export PYTHON_BIN=/data/run01/sczf193/supership-venv/bin/python TRITON_CACHE_DIR=/data/run01/sczf193/.triton/cache PYTHONUNBUFFERED=1 OUTPUT_DIR=output/20261027-113500-runtime-reference; source configs/fastest.env; bash tools/benchmark/evaluate.sh reference --runs 3'`。复现须替换有效作业ID和唯一输出目录，不复用本次输出路径。
- 三轮耗时 `2.870352228 / 1.612564610 / 1.488872158` 秒，中位 `1.612564610` 秒；每轮完整处理200张（batch8，无尾批），6102条检测，官方工具格式检查及逐轮评分成功。reference AP50三轮均0.7809，相对本地参考基线0.7929比值0.984866，98%门槛0.777042、裕量0.003858；仅为本地参考判据，validation/hidden未测。
- 三轮预测字节一致，SHA256 `4185ed612afb8234afae8e31eb43bafd0b68ef32c124d0d510d2da745f29100c`；原始计时日志SHA256 `603aa2d8ae52d93ea7b9620774ee059450d301cfc6f467ed9289cc19ae901e78`；元数据SHA256 `7372e6e602a0f11edf8714c731b63709ada4644eb5feadf76a074ff64554d443`，权重SHA256与下方审查记录一致。环境、全部计时/评分日志、预测及SHA256SUMS仅存本机上述output目录，未上传。候选推荐及Accepted不变，无竞赛提交。

## 20261027-095206-sync-review

- 负责人 Codex /root；分支 main；基于 `99732c143da6658efa4cc4760b68ce9a8c597e78`；审查与 Git 同步状态 completed；GPU 运行状态 blocked（当前为登录节点，无 GPU 分配，查询无空闲 GPU）。本次不是性能优化实验，无竞赛提交。
- 本地原先为无提交、无远程的 Git 目录；已接入 origin/main 历史，保留本地文件后比较。engine/、supership/、run.sh、configs/fastest.env 与云端一致；恢复缺失的 docs/ 和 configs/presets/，修复本地旧 README/台账及忽略规则与当前云端布局不一致的问题。被替换的本地文档保存在 `output/sync-review-20261027-095040/`，仅本机可用。
- 基线权重 SHA256 为 `42a04535d33de94acc58ae3c66a9a2d161e975ee17adae6cae533770d1929c3e`，与 RELEASE_INFO.json 一致。未跟踪的旧实验脚本 `tools/reference/run_further_experiments.py` 含失效路径、过时基线和旧成绩重传逻辑，不运行、不提交；其他已有未跟踪文件保留。
- 使用 `/data/run01/sczf193/supership-venv/bin/python` 尝试默认入口，报错 `Found no NVIDIA driver`；日志 `output/startup-review.log`。全量 pytest 未完成，用户明确节点限制后已终止本会话测试及其子进程，不能记作测试通过。今后包括 CPU 测试在内的任务只在调度分配的 GPU 计算节点执行，规则写入 AGENTS.md。
- reference/validation/hidden AP50 均未测，无新计时结果；最快候选、保守候选与最近 Accepted 不变。下一步：获得 GPU 调度分配后执行 `PYTHON_BIN=/data/run01/sczf193/supership-venv/bin/python bash run.sh --worker` 并通过官方 worker 协议提供输入；在该节点补跑 `python -m pytest -q`。

2026-10-26 按用户要求清理旧实验、结果、重复源码快照和无收益分支。以下仅保留选版依据与代码/参数定位；原始结果已删除，数值为历史记录摘要，本次未重新计时。

| 保留分支 | 依据 | 参数 |
| --- | --- | --- |
| main / exp/supply-eightcore-20261027 | 固定8核推荐6线程，独立8对快15.3459%，8/8胜；完整三轮0.256022902秒Accepted（timing parsed only） | configs/presets/eightcore-thread6.json |
| main历史10线程比较组 | thread100-light，历史完整三轮复测中位 261.305519ms | configs/presets/thread100-light.json |
| exp/continued-sweep-20261026 | 参考集三轮 258.409792 / 256.334286 / 263.016448ms，中位 258.409792ms；8 对快 4.8507%，8/8 胜；reference AP50=0.7809 | configs/presets/thread100-light.json |
| exp/exit-rootcause-20261026 | THP 六对中位 356.261538→289.448907ms；独立三轮中位 285.962649ms；validation AP50=0.9058，32GiB 限制通过 | configs/presets/exit-thp544.json |
| exp/kernel-sweep-20261024 | 历史完整三轮中位 302.713346ms；内核融合十对快 6.70%；validation AP50=0.9058 | configs/presets/kernel544.json |
| exp/rtx4090-e2e | 保守 640 输入、完整 JPEG 解码；validation AP50=0.9167 | configs/presets/conservative640.json |

这些指标来自不同日期/协议比较组，不能据此跨组排名。当前固定8核本地推荐为thread100-light/6线程；非8核环境保留原10线程，保守候选为640完整解码。最近Accepted：2026-10-27 12:38:08，0.256022902秒，仅timing parsed；本轮脱敏回执见上方。此前2026-10-26的0.258409792秒作为历史记录保留，其原始回执已清理。thread100-light及本轮6线程的validation未测；所有hidden AP50未测，官方隐藏集最优未知。

## 清理记录

- ID: 20261026-135116-repository-cleanup；负责人 Codex /root；状态 completed；未使用 GPU，未进行竞赛提交。
- 清理前 main: `fd7d8beae5486299195008bb9ac64cf7a03de51d`。
- 删除旧实验目录、结果/报告/patch、重复源码快照、无收益/诊断分支、闲置 worktree、重复数据下载包、缓存与旧课程笔记本。
- 保留运行源码、模型配置、精选运行参数、测试、公开数据、基线权重、本机凭证和必要文档。
- 未重写历史、未强制推送。普通 Git 提交保留恢复路径；历史文件仍可能占用 Git 对象空间。
- 保留分支的清理前源码 SHA 如下。较早版本的运行协议/依赖以对应源码为准。

- `main`: `fd7d8beae5486299195008bb9ac64cf7a03de51d`
- `exp/continued-sweep-20261026`: `1da325e5a7cf4fe3ff485855622dc22100fd848a`
- `exp/exit-rootcause-20261026`: `6a774ee970eef2fcb32c7a5f01086780700a1e7f`
- `exp/kernel-sweep-20261024`: `d0db0d31148319923efe9eb05fb2ad3f19afa4fd`
- `exp/rtx4090-e2e`: `1c73be3b749dad59a1ec9cc083b115d09cac5ff9`

- 清理检查：主线 126 passed / 44 skipped（可选 GPU/部署相关检查未执行）；shell 语法、参数 JSON 和入口文档链接通过。保留历史分支的 engine/supership/run.sh/模型配置/测试字节未变，已通过差异核对；未重新运行性能计时。
