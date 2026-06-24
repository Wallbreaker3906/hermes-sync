# Browsing boatplus.cn Category Hierarchy

The boatplus.cn product database exposes its full category tree on the product listing page. Use this technique to find correct classifications without asking the user.

## Fetching the Category Tree

```bash
curl -sL "https://www.boatplus.cn/product/product_retrieval_list.html" | python3 -c "
import sys, re
html = sys.stdin.read()
cats = re.findall(r'cat=([0-9_]+)[^>]*>([^<]+)<', html)
seen = set()
for cat_id, cat_name in cats:
    if cat_name.strip() and cat_name.strip() not in seen:
        seen.add(cat_name.strip())
        print(f'{cat_id}: {cat_name.strip()}')
" | sort
```

## Category ID Structure

Categories are encoded as: `一级_二级_三级_`

Example:
- `162_208_255_` = 电气系统 > 船用控制设备 > 其他设备遥测控制系统
- `162_202_766_` = 电气系统 > 船舶自动化 > 船舶综合自动化
- `162_202_220_` = 电气系统 > 船舶自动化 > 移动配载自动控制系统

Note the trailing underscore — category IDs always end with `_`.

## Searching for Specific Products

To check if a product type already exists in the database:

```bash
curl -sL "https://www.boatplus.cn/product/product_retrieval_list.html" | grep -B5 -A10 "关键词"
```

Or filter categories by keyword:

```bash
curl -sL "https://www.boatplus.cn/product/product_retrieval_list.html" | \
  python3 parse_cats.py | grep -iE "遥测|自动化|控制|监测|电气|配电"
```

## Known Category Codes (电气系统, ID=162)

| 二级 | 三级 | ID |
|------|------|-----|
| 船用配电设备 | 主配电板 | 162_260_273_ |
| 船用配电设备 | 应急配电板 | 162_260_272_ |
| 船用液位表 | 液位测量系统 | 162_205_751_ |
| 船用液位表 | 液位开关 | 162_205_752_ |
| 船用控制设备 | 推进控制系统 | 162_208_257_ |
| 船用控制设备 | 液位监测 | 162_208_750_ |
| 船用控制设备 | 其他设备遥测控制系统 | 162_208_255_ |
| 船用控制设备 | 船舶驾驶室集中控制台 | 162_208_248_ |
| 船舶自动化 | 机舱监测报警控制系统 | 162_202_214_ |
| 船舶自动化 | 电力监测系统 | 162_202_215_ |
| 船舶自动化 | 船舶综合自动化 | 162_202_766_ |
| 船舶自动化 | 移动配载自动控制系统 | 162_202_220_ |
| 船舶自动化 | 船舶铺排自动控制系统 | 162_202_213_ |
| 船舶自动化 | 其他设备监测装置 | 162_202_219_ |

## Tips

- The page uses HTTP but redirects to HTTPS — always use `-L` with curl
- Output can be large; pipe through `grep` or Python for targeted extraction
- Category tree is fully loaded in the initial HTML (no JS rendering needed)
