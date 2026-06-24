# 船加网 API 端点

## 认证

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/shop/member/login.do` | POST | 登录，参数：username, password, validcode |
| `/api/shop/member/is-login.do` | POST | 检查登录状态 |
| `/api/shop/member/logout.do` | POST | 登出 |
| `/validcode.do?vtype=memberlogin` | GET | 获取验证码图片（JPEG，160×80） |

登录成功响应：`{"result":1,"message":"登录成功","data":null}`

**注意**：登录需要验证码，验证码通过 macOS Vision OCR 识别。系统使用 openresty WAF，Python requests 会被 403 拦截——必须用 curl。

## 资讯相关

| 端点 | 方法 | 说明 |
|------|------|------|
| `/information/information_zhaobiaoList.html?type=2` | GET | 招标信息列表（需登录） |
| `/api/shop/news/detail.do` | POST | 获取文章详情，参数：id=文章ID |
| `/api/shop/news/collect.do` | POST | 收藏文章 |
| `/api/solr/suggest.do` | POST | 搜索建议，参数：keyword |

## 文章详情 API 响应结构

```json
{
  "result": 1,
  "message": "获取文章详情成功",
  "data": {
    "news_id": 14719,
    "name": "《招标公告》标题",
    "logo": null,
    "news_introduction": "",
    "news_content": "<p>一、采购人：...</p>",
    "create_date": "2026-06-17",
    "attach_file": null,
    "file_name": null
  }
}
```

`news_content` 字段为 HTML，需用正则提取纯文本：
```python
import re
text = re.sub(r'<[^>]+>', '', html_content)
text = text.replace('&nbsp;', ' ').replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
```

## curl 登录示例

```bash
# 全程使用同一 cookie jar
COOKIES=/tmp/bp_cookies.txt
UA="Mozilla/5.0"

# 获取 session
curl -c $COOKIES -s -o /dev/null "https://www.boatplus.cn/"

# 下载验证码
curl -b $COOKIES -c $COOKIES -s -o /tmp/captcha.png \
  "https://www.boatplus.cn/validcode.do?vtype=memberlogin"

# OCR 验证码 → 填入
# 登录
curl -b $COOKIES -c $COOKIES -s \
  -X POST "https://www.boatplus.cn/api/shop/member/login.do" \
  -H "User-Agent: $UA" \
  -H "Referer: https://www.boatplus.cn/login.html" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Origin: https://www.boatplus.cn" \
  --data-urlencode "username=USER" \
  --data-urlencode "password=PASS" \
  --data-urlencode "validcode=CAPTCHA"

# 之后所有请求带上 cookie
# -b $COOKIES -c $COOKIES
```
