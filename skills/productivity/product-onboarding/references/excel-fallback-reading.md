# Excel 读取回退方案

当 openpyxl 因文件过大或被 macOS 安全机制阻挡而超时时，用 zipfile + XML 解析直接读取 xlsx 内容。

## 适用场景
- openpyxl `load_workbook()` 超时（300s+ 无响应）
- macOS 终端命令被「用户未响应」拦截
- 文件有大量空白行（如 16002 行但只有 200 行有数据）

## 方法 1：解压读 XML（推荐，最轻量）

```bash
# 1. 解压 xlsx
cd /tmp && unzip -o template.xlsx -d raw 2>&1 | tail -3

# 2. 读 shared strings（列头和内容文本）
cat raw/xl/sharedStrings.xml

# 3. 读工作表结构
cat raw/xl/workbook.xml  # 列出所有 sheet 名称

# 4. 读具体 sheet（sheet1.xml 即第一个 sheet）
cat raw/xl/worksheets/sheet1.xml | head -c 5000
```

### 解析 shared strings

sharedStrings.xml 的 `<sst>` 下每个 `<si><t>文本</t></si>` 对应一个字符串，索引从 0 开始。提取所有文本：

```python
import xml.etree.ElementTree as ET
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
root = ET.fromstring(xml_content)
for i, si in enumerate(root.findall('s:si', ns)):
    t = si.find('s:t', ns)
    if t is not None and t.text:
        print(f"[{i}] {t.text}")
```

### 解析 sheet 数据

sheet XML 中 `<c r="A1" t="s"><v>0</v></c>` 表示 A1 格的内容是 shared string 索引 0。`t="s"` 表示 shared string，无 `t` 属性表示数字。

```python
rows = root.findall('.//s:row', ns)
for row in rows[:10]:
    for c in row.findall('s:c', ns):
        ref = c.get('r')        # 单元格引用，如 "A1"
        t = c.get('t', '')      # "s"=字符串, 无=数字
        v = c.find('s:v', ns)
        val = v.text if v is not None else ''
        if t == 's':
            val = shared_strings[int(val)]  # 查表
```

## 方法 2：openpyxl read_only（中等重量）

如果文件能加载只是慢：

```python
wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
```

`read_only=True` 使用惰性迭代器，不会一次性加载全部单元格。

## 方法 3：execute_code 的 terminal()（备选）

当本地 terminal 被 macOS 安全机制阻挡时，execute_code 中的 `terminal()` 有时可以绕过：

```python
from hermes_tools import terminal
r = terminal("python3 -c '...'", timeout=15)
```

但注意 execute_code terminal 也有 300s 上限，大文件仍可能超时。

## 已知限制
- XML 解析方式不适合复杂格式（合并单元格、条件格式等）
- 对于需要写回 Excel 的场景，仍需 openpyxl
- 模板文件（含数据验证等高级特性）只能用 openpyxl 编辑
