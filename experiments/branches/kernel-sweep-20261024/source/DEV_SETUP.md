# 隧道、代理、Codex 和 GitHub 一次配置

在运行 Codex 的 Linux 机器上，进入本项目目录执行：

```bash
bash setup_dev.sh
source .local/dev-env.sh
codex
```

首次运行会询问代理地址、隧道方式和 Git 提交身份，保存在被 Git 忽略的 `.local/dev-setup.conf`。之后重复运行同一命令即可，已安装的 Codex 和有效登录会复用。更改参数用 `bash setup_dev.sh --configure`。也可以先将 [配置模板](dev-setup.example.conf) 复制到 `.local/dev-setup.conf`，填写后执行脚本。

脚本依次建立或复用隧道、检查代理访问 GitHub/npm、安装缺少的依赖及 Codex CLI、登录 Codex 和 GitHub、设置 Git 凭证助手及本仓库的提交身份，再验证仓库访问和推送权限。Ubuntu/Debian 缺少依赖时会通过 apt 安装，普通用户可能需要输入 sudo 密码。其他 Linux 系统需要预装 `bash`、`curl`、`git`、`node`、`npm`、`gh`，主动 SSH 模式还需要 `ssh`。npm 安装会校验当前 Codex 包的运行环境要求；如提示 Node 版本不兼容，请先升级 Node。

## 选择隧道方式

**电脑有代理，服务器需要借用电脑的代理（反向隧道）**

先在自己的电脑打开代理客户端（HTTP 或混合端口假设为 `7890`），再在电脑终端执行：

```bash
ssh -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -R 127.0.0.1:17890:127.0.0.1:7890 user@server
```

把 `user@server` 改成服务器登录地址，`7890` 改成电脑实际代理端口。保留该 SSH 连接，在服务器上运行脚本，选择 `existing`，代理地址填写 `http://127.0.0.1:17890`。SSH 使用非默认端口时加 `-p 端口`。服务器不能替电脑发起这个反向隧道；每次断开后需从电脑重新连接。服务器 SSH 配置必须允许端口转发。

**当前机器能够通过 SSH 连接到提供代理的另一台机器（正向隧道）**

选择 `ssh`，填写 SSH 地址、SSH 端口、当前机器监听端口和 SSH 对端的代理端口。脚本用 `ssh -L` 在后台建立隧道，以项目专用控制套接字复用连接，保留主机密钥验证。代理必须是 HTTP/混合端口，不能填写纯 SOCKS 端口。

关闭该后台隧道（SSH 地址替换成配置中的值）：

```bash
ssh -S "$PWD/.local/dev-tunnel.sock" -O exit user@proxy-host
```

更改 SSH 隧道参数前先关闭旧隧道。断线或重启后重新运行脚本恢复连接。

**已经有可用代理**

选择 `existing`，填写真实的 HTTP/混合代理地址即可。脚本不安装代理服务，也不包含代理订阅。

## 登录和后续使用

首次 Codex 登录使用设备码：打开终端显示的链接并完成授权；账号需要允许设备码登录。GitHub 同样需要完成首次网页授权。有效登录会保存到各工具自己的用户配置目录，脚本不复制或输出凭证。无系统密钥环时工具可能使用本机文件保存凭证，请使用自己的系统账号。

每次新开终端执行：

```bash
source .local/dev-env.sh
```

如果需要恢复隧道或检查代理，不想执行安装和登录：

```bash
bash setup_dev.sh --env
source .local/dev-env.sh
```

环境文件只在 `source` 后影响当前终端；脚本不修改 `.bashrc`。Codex 安装到用户专用 npm 目录，不需要 `sudo npm`。Git 身份仅写入当前仓库；`gh auth setup-git` 为当前系统用户配置 GitHub HTTPS 凭证助手。脚本不会自动修改已有的不同 `origin` 地址，也不会提交或推送代码。

配置文件是本机 Bash 文件，只填写可信内容。`.local/` 已被本项目忽略；不要将密码、令牌、`~/.codex/auth.json` 或 GitHub 凭证复制进仓库。

参考：[OpenAI Codex CLI](https://developers.openai.com/codex/cli)、[Codex 登录与远程设备认证](https://developers.openai.com/codex/auth)、[GitHub CLI 登录](https://cli.github.com/manual/gh_auth_login)、[Git 凭证配置](https://cli.github.com/manual/gh_auth_setup-git)。
