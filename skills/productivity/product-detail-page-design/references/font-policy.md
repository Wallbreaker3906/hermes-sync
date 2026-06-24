# 详情页字体商用授权策略

## 硬规则

详情页 HTML/CSS 必须使用阿里巴巴普惠体（Alibaba PuHuiTi），禁止使用任何其他中文字体。

## 字体栈

```css
font-family: 'Alibaba PuHuiTi', 'AlibabaPuHuiTi', 'Alibaba PuHuiTi 2.0', sans-serif;
```

## 为什么不能用 PingFang SC / Microsoft YaHei

| 字体 | 风险 |
|------|------|
| PingFang SC（苹方） | macOS 系统字体，非开源，商业网站展示有潜在争议 |
| Microsoft YaHei（微软雅黑） | 方正字库设计，商业使用需方正授权 |
| **Alibaba PuHuiTi（阿里普惠体）** | ✅ 阿里巴巴开源，SIL OFL 协议，永久免费商用 |

## 安装

macOS 上阿里普惠体通常已预装在 `~/Library/Fonts/`：
- `AlibabaPuHuiTi-2-55-Regular.otf` — 正文
- `AlibabaPuHuiTi-2-85-Bold.otf` — 标题/粗体

## PNG 截图 vs 字体分发

详情页最终输出为 PNG 位图，不嵌入也不分发字体文件。但即便作为静态图片展示，使用明确开源授权的字体可避免任何潜在争议。

## 产品图（800×800）底部标签

产品图底部标签从一开始就使用阿里普惠粗体（Alibaba-PuHuiTi-85-Bold），与详情页正文统一为同一字体家族。
