---
name: boatplus-product-link-finder
description: "从船加网排版任务书中提取跳转链接描述，补全缺失的实际URL。"
version: 1.0.0
---

# 船加网产品跳转链接补全

当用户提供排版任务书（.docx），需要提取其中的跳转按钮链接并补全缺失 URL 时使用。

## 工作流程

### Step 1：读取任务书

任务书通常在 `~/.hermes/shared/` 目录，命名格式如 `倍豪_电气详情图排版任务书.docx`。

```bash
# 复制到 /tmp 避免 TCC 沙盒问题
cp ~/.hermes/shared/XXX排版任务书.docx /tmp/

# 解压 docx 获取 XML（比 python-docx 快，避免大文件超时）
cd /tmp && unzip -o XXX排版任务书.docx -d task_xml/

# 提取纯文本
python3 -c "
import re
with open('/tmp/task_xml/word/document.xml') as f:
    xml = f.read()
texts = re.findall(r'<w:t[^>]*>([^<]+)</w:t>', xml)
print(''.join(texts))
"
```

### Step 2：识别链接需求

任务书末尾通常有链接 URL 清单和分配规则表。提取两类信息：
1. **已有 URL**：任务书直接给出的完整链接
2. **缺失链接**：只有产品类目名称、没有 URL 的条目

### Step 3：登录船加网

```bash
# 获取 cookie + 验证码
curl -c /tmp/bp_cookies.txt -s -o /dev/null "https://www.boatplus.cn/"
curl -b /tmp/bp_cookies.txt -s -o /tmp/captcha_bp.png \
  "https://www.boatplus.cn/validcode.do?vtype=memberlogin&t=$(date +%s)"

# OCR 验证码（Swift Vision）
/tmp/ocr_image /tmp/captcha_bp.png

# 登录（账号：驾驶舱 / 1111）
curl -b /tmp/bp_cookies.txt -c /tmp/bp_cookies.txt -s \
  -X POST "https://www.boatplus.cn/api/shop/member/login.do" \
  -H "Referer: https://www.boatplus.cn/login.html" \
  -H "X-Requested-With: XMLHttpRequest" \
  --data-urlencode "username=驾驶舱" \
  --data-urlencode "password=1111" \
  --data-urlencode "validcode=$CODE"
```

### Step 4：搜索产品 ID

对于缺失链接的产品名称，扫描船加网产品详情页找到对应 ID：

```bash
# 方法1：按品牌搜索（brand=702 是倍豪）
curl -b /tmp/bp_cookies.txt -s \
  'https://www.boatplus.cn/product/product_retrieval.html?brand=702&keyword=液位遥测' \
  | grep -o 'product_detail-[0-9]*.html' | sort -u

# 方法2：扫描详情页 meta keywords 确认产品名
curl -b /tmp/bp_cookies.txt -s \
  'https://www.boatplus.cn/product/product_detail-71903.html' \
  | grep -o 'content="【[^"]*】'
```

### Step 5：区分链接类型

- **详情页链接**：`product_detail-{ID}.html` — 适用于单一 SKU 产品
- **分类检索链接**：`product_retrieval.html?cat={CAT_ID}&brand={BRAND_ID}` — 适用于多 SKU 系列

### Step 6：汇总输出

按「动力」「电气」分表，列出：链接名称、类型、完整 URL、各 SKU 分配规则。

## 已知产品 ID 速查（倍豪 brand=702）

| 产品 | ID | 链接类型 |
|------|-----|---------|
| 液位遥测系统 | 71903 | 详情页 |
| 全船综合控制 IVCS | 71904 | 详情页 |
| 抗横倾系统 | 71905 | 详情页 |
| 阀门遥控系统 | 71906 | 详情页 |
| 推进遥控 BPRCS | 71907 | 详情页 |
| 电力推进系统 | 71985 | 详情页 |
| 泵喷推进器 | 71959 | 详情页 |
| 无轴推进器 | 71958 | 详情页 |
| 无轴推进器 | 71958 | 详情页 |
| 泵喷推进器 | 71959 | 详情页 |
| 全回转推进器 | cat=159_168_192_&brand=702 | 分类检索 |
| 侧向推进器 | cat=159_168_189&brand=702 | 分类检索 |
| 船舶自动化产品 | cat=162_202&brand=702 | 分类检索 |

## Step 7：验证详情页已有链接

当用户要求检查详情图上的引流按钮链接是否正确时：

```bash
# 批量提取产品详情页上的跳转链接（product_detail 和 product_retrieval）
curl -b /tmp/bp_cookies.txt -s \
  'https://www.boatplus.cn/product/product_detail-{PID}.html' \
  | grep -o 'product_detail-71[0-9]*.html\|product_retrieval.html?[^" ]*brand=702[^" ]*' \
  | sort -u
```

> ⚠️ **必须用 `grep -o` 而不是 Python `re.findall`。** Python regex 在这类 HTML 中经常匹配不到（编码/换行差异），`grep -o` 稳定得多。

对比方法：
1. 从任务书中提取每个 SKU 应有的链接（如：链接1→BPRCS, 链接2→自动化, …）
2. 用 grep 提取详情页实际链接
3. 逐条匹配：`product_detail-71907` → BPRCS, `cat=162_202` → 自动化, `cat=159_168_192_` → 全回转, `cat=159_168_189` → 侧推
4. 标记缺失和多余链接

**常见问题**：详情页混入别家品牌的产品链接（如 倍豪 IVCS 页面出现 POSEIDON/博瑞斯 链接）。发现多余链接时，验证其目标产品名：
```bash
curl -b /tmp/bp_cookies.txt -s \
  'https://www.boatplus.cn/product/product_detail-{PID}.html' \
  | sed -n 's/.*<title>\(.*\)|船加网.*/\1/p'
```

## 注意事项

- docx 文件含图片时 python-docx 会很慢，用 unzip + XML 解析更快
- 产品详情页 title 只显示「【倍豪】价格」，真正的产品名在 meta keywords 里
- 验证码识别失败时重新下载重试即可
- Cookie 有效期短，每次新任务需重新登录
- 分类检索链接中的 `cat=` 参数从任务书已有的 URL 中复用
- **⚠️ 区分引流按钮 vs 推荐区链接**：详情页下方的「猜你喜欢」推荐区也会出现其他品牌的产品链接（如 POSEIDON、博瑞斯），这些不是 SKU 详情图里的引流按钮。检查时只关注详情图内嵌的跳转链接，排除页面底部推荐区的跨品牌链接

## ⚠️ 链接检查避坑

用 `grep -o` 抓取页面中的 `product_detail` 和 `product_retrieval` 链接时，抓到的**不全是详情图引流按钮**。船加网产品详情页还有：
- **「猜你喜欢」推荐区**：页面底部的跨品牌推荐（如 POSEIDON、博瑞斯等其他品牌产品）
- **侧边栏分类导航**：通用的产品分类树链接

**正确区分方法**：
- 详情图引流链接：只链向同一品牌（同 brand=702）的产品/分类，且链接数量与任务书规定一致（通常 4 条）
- 推荐区链接：链向不同品牌的产品（如 product_detail-71612.html → 博瑞斯 PRAXIS），这些不是详情图的一部分
- 判断标准：如果某链接指向的 `brand` 参数不是当前品牌、或 product_detail ID 不在当前品牌范围内 → 就是推荐区链接，**不属于引流按钮**
- **⚠️ 链接来源区分**：grep 抓到的页面链接包含三类——①详情图引流按钮（目标）、②侧边栏分类导航（忽略）、③「猜你喜欢」推荐区链接（忽略）。推荐区链接通常指向其他品牌产品（如 POSEIDON/博瑞斯），不要误判为详情图按钮错误
- **grep 优先于 Python 正则**：macOS 终端 `grep -o` 搜索链接比 execute_code 中的 Python `re.findall` 更可靠，后者因 HTML 编码差异（`&amp;` vs `&`）容易漏匹配
