§
宿主环境：macOS 15.7.7 (Apple Silicon arm64)，无 Homebrew，npm 在 ~/.local/bin/npm，git 可用。DeepSeek provider，已配 GITHUB_TOKEN。
§
两个 QQ Bot 通过 Profile 架构运行：Bot① 1904086414（default），Bot② 1904114200（qqbot2）。各独立 Gateway+launchd+健康检查。休眠后自动恢复。都不要 ALLOW_ALL_USERS=true。QQ Open ID 各应用独立。
§
用户不是程序员，偏好通俗易懂、非技术性的 Hermes 使用案例。喜欢可视化网页形式（深色科技风，点击展开详细步骤）。已搭建每日案例系统：每天早上 9:00 推送 2-3 个跨行业案例到 QQ，网页累积更新并自动推送到 GitHub（Wallbreaker3906/hermes-cases）。GitHub Pages 链接用于分享给朋友。
§
企业微信：组织 ww4c75bd5437198158，智能机器人 Bot 已接入 Hermes（WebSocket）。但不支持客户联系功能，需自建应用模式（需公网URL），用户计划改天研究。
§
GitHub 仓库 hermes-cases 位于 ~/.hermes/hermes-cases/，密钥认证。推送不要切 remote URL（HTTPS易残留超时）。
§
用户工作：船加网boatplus.cn产品数据+客户运营——①产品入驻（PDF→分类→SKU，已处理倍豪/欧卡）；②会员权益履约（黄金/铂金会员广告、推文、船单、E-news、商机对接，Excel追踪）。SKU：一个型号=一个。收到文件勿预设与入驻有关。
§
用户提供的 Excel 数据可能有录入笔误（如单位 g/kg 混淆、数字缺位等），发现疑点应主动提出核对，不要盲从。用户鼓励这种质疑。
§
打开文件用Microsoft Excel，不用WPS。WPS macOS app名`wpsoffice`。
§
OCR：Swift PDFKit+Vision（ocr-and-documents技能），TCC绕过用osascript Finder dup→/tmp。Playwright已装。
§
macOS 沙盒：Desktop 写入权限不稳定（TCC 间歇拦截 Python/shell），工作文件优先存 ~/Documents/。openpyxl 写复杂 Excel 模板会丢数据验证规则，Excel 打开时弹修复提示但核心数据完整。
§
欧卡智舶：品牌色#13907a/#213e56。沧巡无人艇2SKU(汽油/电动增程)，分类S_01_008。海况：工作3级/生存4级（非PDF的4/5，用户已纠正）。详情页规则不变。
§
详情页热区流程见 detail-page-hotspot-extraction 技能。Actisense品牌ID=685，产品ID 71720-71735。
§
复用型文档第一时间存 ~/Documents/，不在缓存目录久留。命名格式：【企业名】文档内容_YYYYMMDD.xlsx。当前：欧卡黄金会员权益履约追踪表在 ~/Documents/【欧卡】黄金会员权益履约追踪_20260616.xlsx。
§
权益履约追踪表规则：①进度分四级——未申请/已申请/进行中/已完成。「已申请」=权益已启用、有部分完成但剩余未启动；「进行中」=当前正在推进。②I列(完成情况简述)面向客户，仅「已申请」「已完成」时填写；「未申请」「进行中」留白。③铂金会员模板：~/Documents/【模板】铂金会员权益事项说明_20260616.xlsx。
§
文档字体：Word默认宋体/微软雅黑；详情页PNG必须用思源/阿里普惠等开源商用字体，禁用系统专有(PingFang等)。答案不确定时必须标注来源及风险，不给无依据的确定性结论。
§
共享目录 ~/.hermes/shared/ 可绕过沙盒读写，永久保留不被清理，已加 Finder 侧边栏。用户无 iCloud Drive 选项，远程备份用 Git 私有仓库。后需用户手动放入工作文件。
§
船加网详情页含"猜你喜欢"推荐区，其链接非SKU引流按钮。检查引流按钮时排除推荐区链接。
§
常玻(supplierID=131)：常州玻璃钢造船厂有限公司。船舶建造→水上运动休闲→游览船(003)。2SKU：CB2600仿古(排序2580,后6位000004)、CB2800新能源(排序2581,后6位000005)。船舶建造排序最后=2583，新增从2584起。后6位按三级分类编号：游览船(003)最后=000005；无人艇(008)最后=000028(欧卡沧巡000027-28)。
§
两台Mac间同步：私有仓库 Wallbreaker3906/hermes-sync（SSH: id_ed25519_hermes）。本地 ~/.hermes/sync/ 存 memories/ skills/ config.yaml。换电脑前说「同步一下」=push，换后说「同步一下」=pull。旧电脑明天开机后首次克隆。
