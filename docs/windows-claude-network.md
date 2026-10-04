# Windows Claude 地区信号审计与日本出口配置

更新日期：2026-10-04。适用范围：Windows、Clash Verge Rev / Mihomo、Edge、CMD、PowerShell 和 Claude Code。

本文记录一套实际实施过的网络与浏览器隐私配置逻辑，供交流和复现。公开版省略个人公网 IP、代理节点地址、订阅凭证、账号、设备标识和本机绝对路径。本文不是一键安装包，也不保证账号不会受到服务限制。

## 1. 目标与判断原则

- Claude 使用已验证的日本出口，固定分组，避免国家随机切换和失败后直连。
- 检查 HTTP、DNS、IPv6、WebRTC、语言和时区等不同信号，逐项验证。
- 保留中文界面，将时区和地区设为日本，网页首选语言设为日语、英语。
- 每次修改前备份，只在验证通过后保存；失败时恢复上一份可用配置。

日本 HTTP 出口不能证明 UDP 安全，启用 TUN 也不能代替 WebRTC 实测。清除本地站点数据不能删除服务端已有记录。中文内容、姓氏、字体和设备品牌都不能单独证明国籍或所在地，不应把社区猜测写成确定的封号规则。

## 2. 网络结构

```text
Claude 专用 Edge / Claude Code
  → 本机专用代理入口 127.0.0.1:17997
  → Claude-Japan 单节点分组
  → 已验证的日本公网出口

普通终端 / 系统 HTTP 客户端
  → 通用代理入口，例如 127.0.0.1:7897
  → Mihomo 规则分流；Claude 域名进入 Claude-Japan

常规 DNS
  → Cloudflare DoH
  → Claude-Japan
```

端口仅为本次配置的约定，移植时应检查占用并统一修改。专用入口只监听回环地址，避免暴露为局域网代理。

### Claude 分组与失败行为

使用 `select` 分组，只放一个经过实际验证的日本节点，省略 DIRECT 和其他国家备选。全局增强脚本在每次生成配置时检查节点是否存在，缺失时把分组设为 REJECT。

为专用 mixed listener 设置 `proxy: Claude-Japan`，使这个入口的所有连接都进入固定分组。普通入口另设 Claude/Anthropic 域名和客户端进程规则。域名规则不是永久完整清单，新增的认证、内容或第三方域名仍需检查；专用入口可减少遗漏域名产生的出口分歧。

节点名称固定不等于公网 IP 固定。远端 IPv4/IPv6 地址可能轮换，应同时检查国家和节点状态。

### 官方入站 IP 网段补充规则

在现有域名规则附近，加入以下 Mihomo 规则，并保留在订阅增强脚本中：

```yaml
- IP-CIDR,160.79.104.0/23,Claude-Japan,no-resolve
- IP-CIDR6,2607:6bc0::/48,Claude-Japan,no-resolve
```

这些是 Anthropic 官方公布的入站 IPv4、IPv6 网段。规则应优先于广泛的地区分流规则，并保留原有直连例外的优先级。它们补充已有域名分流，不能替代 DNS、浏览器和额外服务地址的检查。[官方 IP 地址说明](https://platform.claude.com/docs/en/api/ip-addresses)

已核对规则加载，并用官方 IPv4 地址保持原域名的 TLS 校验，确认实际连接命中此 CIDR、进入 Claude-Japan。IPv6 规则已加载，公网 IPv6 流量尚未验证。

## 3. DNS 与启动依赖

检查这些字段，不只查看 Windows 网卡 DNS：

```text
dns.nameserver
dns.nameserver-policy
dns.default-nameserver
dns.proxy-server-nameserver
dns.proxy-server-nameserver-policy
dns.direct-nameserver
dns.fallback
```

本次将常规解析统一设置为：

```yaml
nameserver:
  - https://1.1.1.1/dns-query#Claude-Japan
  - https://1.0.0.1/dns-query#Claude-Japan
```

其余解析策略也使用这个日本分组，并移除国内解析器、回指自身的节点解析与不需要的 fallback。DNS 使用 TCP 上的 DoH，未开启 HTTP/3 优先。Cloudflare 的公共 1.1.1.1 解析器不向权威服务器发送 ECS；不应把所有 DNS 提供商都推定为相同行为。[Cloudflare FAQ](https://developers.cloudflare.com/1.1.1.1/faq/)

### 避免循环依赖

如果代理连接地址是域名，不能简单要求“解析这个节点也必须经过这个尚未连接的节点”。本次尝试的直连境外加密启动解析没有通过连接测试，已回滚。

最终方案是：在日本代理仍正常时，通过它加密解析节点连接域名，将其中一个有效入口 IPv4 地址保存到增强脚本；节点连接使用这个地址，随后其他 DNS 均可经过日本分组。保存时同时记录对应域名，订阅更换域名时不继续冒用旧地址。

该方案需要维护：提供商更换入口 IP 后须重新验证并更新固定地址；过期地址会造成连接失败。不要取消 TLS 校验，也不要为了恢复连接偷偷增加直连 DNS fallback。这种入口地址与日本公网出口地址是两个不同概念。

### Windows 网卡 DNS

另外检查 WLAN 等物理适配器的 DNS。仅修改它不能替换 Mihomo 内部解析器。

本次把 WLAN IPv4 DNS 改为 `1.1.1.1`、`1.0.0.1`，设置对应的 Windows DoH 模板为 `https://IP/dns-query`，启用 `AutoUpgrade`，禁用 `AllowFallbackToUdp`。相关命令需要管理员权限，其他 Windows 版本须先确认支持这些设置。保存原来是 DHCP 还是静态 DNS，恢复时按原方式处理。

移植到不支持这些 DoH 命令的 Windows 10 时，应由 Mihomo 的加密解析和 TUN DNS 接管提供保护。仅把网卡 DNS 改成 Cloudflare 地址不会自动启用加密；停止 Mihomo/TUN 后，这层保护也不能视为仍然有效。

## 4. 终端、浏览器与系统

### CMD / PowerShell / Claude Code

系统代理、WinHTTP 和代理环境变量是不同设置，各类程序对它们的支持也不同。本次检查并补齐：

- 当前用户的 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`。
- CMD 的 AutoRun，以及 PowerShell 7 用户启动配置。
- WinHTTP 代理和 Windows 用户代理。
- Claude Code 用户配置中的专用 HTTP/HTTPS 代理。
- `NO_PROXY` 只保留需要直连的回环地址。

不能只看到环境变量存在就认定程序已使用代理。已有终端须重开，各客户端应单独测试。系统代理和通用终端变量也可能影响其他程序；优先在 Claude 专用配置或启动环境中设置代理，实施全局配置时另行评估影响范围。[Claude Code 网络文档](https://code.claude.com/docs/en/network-config)

### Edge

使用独立数据目录作为 Claude 专用配置，避免复用旧配置的站点存储。入口显式指定专用代理、禁用 QUIC、限制 WebRTC、拒绝地理定位，网页语言预设为 `ja,en`。

本次另写入全局策略：

```text
WebRtcIPHandlingUrl（REG_SZ）
[{"handling":"disable_non_proxied_udp","url":"*"}]

DefaultGeolocationSetting（REG_DWORD）
2
```

把 WebRTC 策略扩为全部来源，是因为仅匹配 Claude 来源的策略不能直接约束本地检查页或其他来源。可进一步增加仅针对已安装 `msedge.exe` 的出站 UDP 阻止规则，适用所有防火墙配置文件。**不要阻止整个系统 UDP**，以免影响其他应用。浏览器音视频、QUIC 或局域网功能可能受到这个限制影响。[Edge WebRTC 策略](https://learn.microsoft.com/en-us/deployedge/microsoft-edge-policies/webrtciphandlingurl)

浏览器 Preferences 只能在浏览器完全退出后修改并备份。修改注册表已有键时不要用 `New-Item -Force` 重建它，以免覆盖其他策略；应只在键不存在时创建，再修改指定值。含中文的 PowerShell 脚本使用带 BOM 的 UTF-8，兼容系统 Windows PowerShell。

### 时区、地区、语言和位置

本次设置东京时区（UTC+9）、日本地区与区域格式，保留中文界面和输入法。关闭当前用户不需要的位置访问权限。

网页 `Accept-Language`、`navigator.languages`、`Intl` locale、浏览器显示语言和 Windows 区域格式并不是同一个值。配置文件写入成功不能代替实际网页请求头检查；中文界面保留时，某些 locale 仍可能显示中文。

## 5. 验证顺序与本次证据

1. 校验生成的 Mihomo 配置，再检查实际加载的分组、规则和 TUN 状态。
2. 分别测试 CMD、PowerShell、专用代理入口和显式不使用 HTTP 代理的 TUN 路径。
3. 请求 `https://claude.ai/cdn-cgi/trace`，检查 `loc` 与 `colo`；本次多个路径为 JP/NRT。
4. 检查 DNS 解析结果、IPv6 地址与路由；没有可用公网 IPv6 路径时，应记录未验证，不能把连接失败当成防泄漏证明。
5. 在实际使用的浏览器配置中检查语言、时区、实际请求头和 WebRTC/STUN。
6. 以管理员权限短时抓取物理网卡流量，分清 TUN 内部流量与物理出口。不得停止已有采集任务或删除他人的筛选器。

本次修改前，普通 Edge 的本地 STUN 测试曾取得与日本 HTTP 出口不同的中国登记公网地址。日本节点配置为 `udp:false`，不能单凭把它改为 `true` 就认定服务端支持 UDP。

修改后已核对全局 WebRTC、定位策略和 Edge UDP 防火墙规则。短时 NIC 抓包的筛选范围是端口 53 与 UDP 19302，匹配数据包数为 0。由于期间没有浏览器 STUN 复测，**不能把这个 0 当成 WebRTC 已无泄漏的完整证据**，也不能证明所有 DNS 协议与应用都安全。

浏览器工具当时没有可用 Edge 连接，因此新策略的实际加载、语言请求头、WebRTC 候选地址和已登录 Claude 功能尚未完成验证。应手动重开 Edge、查看 `edge://policy` 并复测。

## 6. 备份、恢复与公开分享

本地备份应保存原代理变量、启动配置、浏览器设置、DNS 模式、DoH 参数、位置许可、Clash 配置与分组选择，以及本次创建的防火墙规则名。恢复时只删除自己创建的规则。

恢复脚本必须与对应设备的备份配套，不能把某台设备的恢复脚本当成通用安装包。恢复前须退出 Edge，并使用原用户账号提升权限。本仓库说明文档不包含本机备份或一键安装/恢复脚本。

公开分享本文即可，不要连同真实订阅、包含代理密码的完整配置、Cookie、账号资料、原始抓包、本机备份或未脱敏的诊断结果一起发布。

本地配置不能清除服务端登录历史、支付资料或账号关联。没有执行硬件标识伪造、字体删除、身份资料修改，亦没有配置整机代理停止后的断网机制。WSL、容器、虚拟机和其他设备须独立验证。

## 参考资料

- [Mihomo 分流规则与优先级](https://wiki.metacubex.one/en/config/rules/)
- [Mihomo DNS 配置与代理参数](https://wiki.metacubex.one/en/config/dns/)
- [Claude Code 网络配置](https://code.claude.com/docs/en/network-config)
- [Edge WebRTC 策略](https://learn.microsoft.com/en-us/deployedge/microsoft-edge-policies/webrtciphandlingurl)
- [Edge 定位策略](https://learn.microsoft.com/en-us/deployedge/microsoft-edge-policies/defaultgeolocationsetting)
- [Cloudflare 公共 DNS FAQ](https://developers.cloudflare.com/1.1.1.1/faq/)
