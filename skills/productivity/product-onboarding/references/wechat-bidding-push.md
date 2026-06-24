# 微信招标/中标公告推文生成

从船加网抓取招中标资讯，排版为微信公众平台可发布的推文。

## 整体流程

```
1. 登录船加网（curl + CAPTCHA OCR）
2. 访问招中标列表页 → 解析 HTML
3. 按日期区间筛选 + 按类型分组（招标 / 中标）
4. 逐篇抓取详情页全文
5. 按微信推文格式排版输出
```

## 关键规则

- **招标公告和中标公告是两篇独立的推文**，不能混在一起
- 一篇推文通常包含同一日期区间内的多条公告
- 排版格式参照船加网现有推文风格（参见下方模板）

## 列表页解析

URL: `https://www.boatplus.cn/information/information_zhaobiaoList.html?type=2`

HTML 结构（每个条目的 class: `newsList-left`）：
```html
<div class="newsList-left">
    <a href="information_zhaobiaoDetail.html?id=14719">
        <div><h4>《招标公告》标题文字</h4></div>
    </a>
    <div>
        <div class="newsList-leftTime">
            <span>2026-06-17 </span>
        </div>
    </div>
</div>
```

**解析要点**：
- 用 `id=` 后的数字匹配 `2026-06-\d{2}` 日期
- `<h4>` 内容中 `《招标公告》` vs `《中标公告》` 区分类型
- 列表页只显示前 10 条，有「查看更多」按钮（不在此次日期区间内的忽略即可）

## 详情页抓取

URL: `https://www.boatplus.cn/information/information_zhaobiaoDetail.html?id={id}`

需要携带登录后的 session cookie。正文内容通常在页面的主要内容区域。用 curl 抓取后提取 HTML 中的文本正文，移除导航/页脚等噪声。

## 微信推文排版模板

参照船加网现有推文风格（以招标公告为例）：

```
{总标题，如「船加网招标资讯 | 2026年6月15日-6月17日」}

项目概况

-------------------

1. {公告标题一}

{小标题，如「项目概况」}
{正文内容}

2. {公告标题二}

{小标题}
{正文内容}

...

-------------------

招标信息：请扫描下方二维码登录查看
长按下方二维码查阅完整招标信息
```

**排版要点**：
- 总标题：日期区间明确
- 顶部标注「项目概况」
- 正文用 **1. / 2.** 编号分节
- 每节有**小标题加粗**
- 公告间用分隔线隔开
- 段尾引导读者扫码查看完整信息
- 正式公文风格，无多余装饰

## 登录 cookies 管理

Cookies 文件用 curl 的 `-c` 创建和 `-b` 复用：
```bash
# 初始化 session
curl -c /tmp/bp_cookies.txt -s "https://www.boatplus.cn/" > /dev/null

# 后续请求都带 -b /tmp/bp_cookies.txt -c /tmp/bp_cookies.txt
```

cookie 文件在登录后包含完整的认证 session，可在同一 shell 会话中持续复用。
