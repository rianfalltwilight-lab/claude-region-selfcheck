# Claude Region SelfCheck

面向 Claude 用户的本地浏览器地区信息检查工具。**这是一个由 Codex 协助完成的 vibe coding 项目，不是 Anthropic 官方工具，也没有经过独立安全审计。** 用它观察环境变化，不把结果当作封号预测或账号安全保证。

无需账号、API Key、管理员权限或前端构建。支持 Edge、Chrome 等提供相关浏览器 API 的浏览器。默认对照日本时区与日语/英语；其他地区可自行调整。

## 最快开始：直接打开

1. 点击 GitHub 的 **Code → Download ZIP**，解压项目。
2. 开启自己已配置好的代理，在**实际登录 Claude 的浏览器配置**中打开 `Browser-Region-SelfCheck.html`。不要用另一个浏览器的检查结果代表 Claude 浏览器。
3. 查看卡片与下方 JSON，点击 **运行 WebRTC/STUN 检查**，等待最多 10 秒。
4. 点击 **打开 Claude 出口检查**，在新页查看 `loc`；日本预期为 `JP`。`colo` 是 Cloudflare 接入机房，不是实际所在城市证明。
5. 点击 **保存检查结果**，修改配置后再次保存，比较前后变化。

文件模式不能读取实际 HTTP 请求头。如需 `Accept-Language`，使用下面的本地服务模式。

## 本地服务模式：读取请求头和 .env

需要 Python 3.9 或更新版本，仅使用标准库，无需 `pip install`。

Windows PowerShell / CMD，在解压目录运行：

```powershell
copy .env.example .env
python server.py
```

macOS / Linux：

```sh
cp .env.example .env
python3 server.py
```

然后在 Claude 所在的浏览器配置中打开 **http://127.0.0.1:18765**。终端按 `Ctrl+C` 停止。端口占用时修改 `.env` 中的 `SELFCHECK_PORT`。服务只接受回环地址，不提供目录浏览，不返回 `.env`。

`.env` 只在启动时读取；修改后重启服务。操作系统环境变量优先于 `.env`。**直接打开 HTML 不读取 `.env`**；文件模式需要修改 HTML 内的 `settings` 默认值。

## 结果怎么看

| 项目 | 日本配置的对照值 | 如何理解 |
| --- | --- | --- |
| `timeZone` | `Asia/Tokyo` | 浏览器返回的时区；卡片只比较它是否等于目标值 |
| `utcOffsetMinutes` | `540` | 此工具定义为 UTC 以东的分钟数，即 UTC+9 |
| `languages` | 例如 `ja,en` 或 `ja-JP,en` | 网页首选语言；中文 UI、locale 或中文内容不能单独判定地区 |
| `requestHeaders.Accept-Language` | 例如 `ja,en;q=0.9` | 仅服务模式可读取；这是发给本地服务的请求头 |
| `webRTC.candidates` | 逐条查看 `type`、`address` | `host` 常为本地地址，`srflx` 通常是 STUN 发现的映射地址，`relay` 为中继地址；工具不自动查询地址国家 |
| `webRTC.status` | 收集完成 / 等待超时 / 检查失败 | 表示运行状态，不能当作“通过/不通过”；需结合候选地址与错误判断 |
| 出口检查页 `loc` | `JP` | 表示该次 Claude 域名 HTTP 请求的出口国家；应在同一浏览器配置中打开 |
| Canvas / WebGL / 音频摘要 / 字体 | 没有“日本合格值” | 用于观察浏览器环境变化，不提供国籍或风险评分 |

看到意外公网地址时，先核对该地址归属及浏览器 WebRTC/代理策略，再复测。DNS、ECS、所有 IPv6 路径及 Claude Code 网络不由这张浏览器页面自动验证。浏览器页面和 CLI 是不同客户端，需要分别检查。

## 给其他使用者预设的环境变量

仓库提供 `.env.example`，复制后填写自己的配置：

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `SELFCHECK_HOST` | `127.0.0.1` | 本地服务监听地址，仅允许回环 |
| `SELFCHECK_PORT` | `18765` | 本地服务端口 |
| `SELFCHECK_EXPECTED_TIMEZONE` | `Asia/Tokyo` | 页面时区对照目标，不修改系统时区 |
| `SELFCHECK_EXPECTED_LANGUAGES` | `ja,en` | 页面语言对照目标，不修改浏览器首选语言 |
| `SELFCHECK_STUN_URL` | `stun:stun.l.google.com:19302` | 点击按钮后联系的 STUN 服务器 |
| `SELFCHECK_RTC_TIMEOUT_MS` | `10000` | 候选地址收集等待时限，允许 1000–60000 |
| `CLAUDE_PROXY_URL` | 留空，需自行填写 | 可选 Claude Code 启动器的 HTTP/HTTPS 代理；例如 `http://127.0.0.1:7897` |
| `CLAUDE_NO_PROXY` | `localhost,127.0.0.1,::1` | 可选启动器的回环直连列表 |
| `CLAUDE_TZ` | `Asia/Tokyo` | 可选启动器给子进程设置的 `TZ`；不修改 Windows 或浏览器时区 |

**本工具不附带代理节点，也不会把填写的代理自动变成日本出口。** 先在自己的代理客户端中设置并验证出口，再填写本地代理地址。代理端口每个人可能不同；7897 只是示例。

### 可选：用同一份 .env 启动 Claude Code

已安装原生 Claude Code 并加入 PATH 的用户，可填写 `CLAUDE_PROXY_URL` 后运行：

```powershell
python launch_claude.py
```

参数直接传给 Claude，例如 `python launch_claude.py --version`。启动器只修改这个子进程的环境，不写全局系统代理、不改系统 DNS 或注册表；未填写有效 HTTP 代理会停止启动。它会清除继承的大小写代理变量，再设置 `HTTP_PROXY`、`HTTPS_PROXY`、`NO_PROXY`，避免旧变量覆盖新值。

也可参照 `claude-settings.example.json`，将其中的 `env` 字段**合并**到自己的 `~/.claude/settings.json`，保留原配置。改成自己的代理端口，不要直接覆盖整个已有文件。后台会话的网络变量建议放在用户 settings；正在运行的会话需重新启动才能读到新环境。具体支持范围见 [Claude Code 官方网络文档](https://code.claude.com/docs/en/network-config)。

浏览器不会自动继承上述 CLI 代理配置。网页语言、系统地区与时区仍需使用者在各自系统和浏览器中设置。

## 隐私与项目范围

基础检测在浏览器本地运行，没有分析 SDK、账户登录或结果上传接口。点击 WebRTC 按钮会联系指定 STUN；点击出口按钮会打开 Claude 的 Cloudflare trace 页面。JSON 由用户主动保存，可能包含 IP、用户代理及设备特征，分享前请自行脱敏。

本项目提供检查工具与配置示例，不包含个人节点、订阅、Cookie、原始抓包或本机备份。`.env` 和下载的诊断 JSON 已列入 `.gitignore`。

网络配置思路见 [Windows Claude 网络配置说明](docs/windows-claude-network.md)。它是人工配置参考，按自己的系统版本调整，不能直接视为通用安装脚本。

## Vibe coding 与维护

这个项目通过描述需求、AI 编写代码和人工验证迭代完成。欢迎 fork、查看源码、提交问题或改进；新浏览器版本、策略和网络环境可能改变检测表现。提交问题时附浏览器版本、运行方式和脱敏后的结果即可。

开发检查：

```sh
python -m unittest discover -s tests -v
node --test tests/test_page.js
```

Python 检查需要 Python 3.9+，JavaScript 检查需要 Node.js 18+；日常使用页面不需要 Node.js。目前包含配置校验、代理环境隔离、本地 HTTP 路由、配置注入以及浏览器 API 不可用时的错误处理检查；JavaScript 使用模拟环境，实际 STUN、公网出口、DNS 和 IPv6 需要在自己的环境中复测。

MIT License。

## 参考

- [MDN：WebRTC 候选地址类型](https://developer.mozilla.org/en-US/docs/Web/API/RTCIceCandidate/type)
- [Claude Code：网络配置](https://code.claude.com/docs/en/network-config)
- [Anthropic：API IP 地址](https://platform.claude.com/docs/en/api/ip-addresses)
