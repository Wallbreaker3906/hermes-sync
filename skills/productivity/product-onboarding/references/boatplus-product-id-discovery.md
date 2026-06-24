# 船加网产品详情页 ID 查找技巧

## 场景

排版任务书中列出了跳转链接的产品类目名称（如「液位遥测系统」「推进遥控 BPRCS」），但没有给出实际 URL。需要在船加网上找到对应的产品详情页链接。

## 方法：ID 区间扫描 + Meta Keywords 识别

船加网的产品详情页 URL 格式为 `product_detail-{id}.html`。同一供应商的产品 ID 通常集中在连续区间（如倍豪的 71903-71985）。

### Step 1：确定 ID 区间

从任务书已有的 URL 推断品牌 ID 区间。如动力任务书给了一个 `product_detail-71985.html`，则扫描 71900-71990。

### Step 2：批量检查页面标题

```bash
for pid in 71903 71904 71905 71906 71907; do
  title=$(curl -b /tmp/bp_cookies.txt -s \
    "https://www.boatplus.cn/product/product_detail-$pid.html" \
    | sed -n 's/.*<title>\(.*\)|船加网.*/\1/p')
  echo "ID=$pid: $title"
done
```

**陷阱**：部分产品的页面 title 只显示 `【品牌】价格`，不显示产品名。这是因为产品名未填入 title 标签。

### Step 3：对无名产品查 Meta Keywords

当 title 无法识别产品名时，检查 `<meta name="keywords">`：

```bash
curl -b /tmp/bp_cookies.txt -s \
  'https://www.boatplus.cn/product/product_detail-71903.html' \
  | grep -o 'content="[^"]*液位[^"]*\|content="[^"]*阀门[^"]*\|content="[^"]*横倾[^"]*"'
```

Keywords 格式：`【产品名】,【产品名】价格,【品牌】,【品牌】【产品名】`

### Step 4：多关键词并行查询

如果要一次查多个可能的产品名：

```bash
for pid in 71905 71906; do
  echo "=== $pid ==="
  curl -b /tmp/bp_cookies.txt -s \
    "https://www.boatplus.cn/product/product_detail-$pid.html" \
    | grep -o 'content="[^"]*关键词1[^"]*\|content="[^"]*关键词2[^"]*"'
done
```

## 完整案例：倍豪电气产品 ID 发现

| ID | Title 显示 | Keywords 揭示 | 产品名 |
|----|-----------|--------------|--------|
| 71903 | 【倍豪】价格 | 液位遥测系统 | **液位遥测系统** |
| 71904 | 【倍豪】价格 【IVCS】 | — | 全船综合控制系统 IVCS |
| 71905 | 【倍豪】价格 | 抗横倾系统 | **抗横倾系统** |
| 71906 | 【倍豪】价格 | 阀门遥控系统 | **阀门遥控系统** |
| 71907 | 【倍豪】价格 【BPRCS】 | — | 推进遥控系统 BPRCS |

> 加粗的 3 个是通过 Keywords 才识别出的——仅看 title 无法区分。

## 技巧

- 需要登录态 cookie（`-b /tmp/bp_cookies.txt`），先完成登录流程
- ID 区间推断：已知 1 个产品 ID → 扫描 ±50 范围通常够
- 排除非目标品牌：检查 title 中是否包含目标品牌名（如「倍豪」）
- 页面返回 200 但 title 不含品牌名 → 该 ID 属于其他供应商，跳过
