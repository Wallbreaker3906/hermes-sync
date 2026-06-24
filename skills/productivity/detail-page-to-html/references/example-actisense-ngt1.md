# Actisense NGT-1 详情页案例

## 图片信息
- 文件名: 39534770.png
- 尺寸: 1660×7617 (@2x, 容器 830px)
- 产品: Actisense NGT-1 (NMEA 2000 to PC Interface)

## 检测结果: 5 个显式热区，0 个隐式热区

| # | 指示文字 | OCR位置(归一化) | 容器边界(像素) | HTML坐标 |
|---|---------|---------------|--------------|---------|
| ① | 点击了解 NMEA 2000网络 | (0.146,0.988) | (141,20)→(608,130) | 70,10,304,65 |
| ② | 点击此处查看 Actisense专属软件 | (0.142,0.661) | (175,2490)→(1552,2600) | 87,1245,776,1300 |
| ③ | 点击此处查看 更多网关设备 | (0.578,0.390) | (863,4560)→(1627,4680) | 431,2280,813,2340 |
| ④ | 点击此处查看全部 | (0.142,0.055) | (130,7040)→(659,7280) | 65,3520,329,3640 |
| ⑤ | 点击此处查看 | (0.154,0.022) | (130,7280)→(1089,7540) | 65,3640,544,3770 |

## 容器检测关键数据

热区① 验证（与用户手动标注对比）：
- 用户预期 HTML X: 70→306 (像素 140→612)
- 检测结果 HTML X: 70→304
- 偏差: 左侧 0px, 右侧 -2px ✓

容器检测参数:
- sensitivity=12 (捕获渐变阴影)
- dev_run>=3 (容忍薄装饰线)
- 底色采样位置: 文字外侧 50-100px

## 最终代码

```html
<img src="https://www.boatplus.cn/statics/attachment/ueditor/XXXX/XX/XX/X/39534770.png" border="0" usemap="#ngt1_hotspots" alt="Actisense NGT-1" style="width:830px;" />

<map name="ngt1_hotspots">
  <area shape="rect" coords="70,10,304,65" href="产品链接1" target="_blank" />
  <area shape="rect" coords="87,1245,776,1300" href="产品链接2" target="_blank" />
  <area shape="rect" coords="431,2280,813,2340" href="产品链接3" target="_blank" />
  <area shape="rect" coords="65,3520,329,3640" href="产品链接4" target="_blank" />
  <area shape="rect" coords="65,3640,544,3770" href="产品链接5" target="_blank" />
</map>
```
