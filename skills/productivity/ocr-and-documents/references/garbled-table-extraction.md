# Garbled Table Extraction via Coordinate-Based Text Blocks

## Problem

When `page.get_text()` returns garbled/overlapping table data (common in PDFs with image backgrounds, dual-layer text, or complex layouts), raw text extraction mixes columns and rows together, making tables unreadable.

**Example**: A clean-looking table in the PDF renders as:
```
BP-25CcBP.35c P45ePs0cP6ocBP70CC| ePsoC BP.SOCBPi5oc
2400KW 77000 20320 3400 4500HW 5100KW 6200KW 700004 1200084
1800rpm 1000/1200P1000/1200p 750pm 750pm 750pm 560/750pm 750rpm oo
```

The model names, power values, and RPM values are all concatenated and misaligned.

## Solution: Position-Based Block Extraction

Use `page.get_text("dict")` to get each text span with its bounding box (`bbox = [x0, y0, x1, y1]`), then group by row (y-coordinate) and sort by column (x-coordinate):

```python
import pymupdf

doc = pymupdf.open("document.pdf")
page = doc[page_num]

blocks = page.get_text("dict")["blocks"]

for block in blocks:
    if block["type"] == 0:  # text block
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if text:
                    bbox = line["bbox"]
                    # bbox[0] = x, bbox[1] = y, bbox[2] = x+w, bbox[3] = y+h
                    print(f"y={bbox[1]:.0f}, x={bbox[0]:.0f} | {text}")
```

## Grouping into Table Rows

Text at similar y-coordinates (±tolerance) belongs to the same table row. Sort each row by x-coordinate to reconstruct column order:

```python
# Collect all spans with positions
spans = []
for block in page.get_text("dict")["blocks"]:
    if block["type"] == 0:
        for line in block["lines"]:
            bbox = line["bbox"]
            text = "".join(s["text"] for s in line["spans"]).strip()
            if text:
                spans.append({"y": bbox[1], "x": bbox[0], "text": text})

# Group by row (y within 10px tolerance)
rows = {}
for s in spans:
    y_key = round(s["y"] / 10) * 10  # quantize y
    if y_key not in rows:
        rows[y_key] = []
    rows[y_key].append(s)

# Print each row, sorted by x
for y_key in sorted(rows.keys()):
    row = sorted(rows[y_key], key=lambda s: s["x"])
    print(f"Row y≈{y_key}: {' | '.join(s['text'] for s in row)}")
```

## Column Alignment

Once rows are separated, align columns by matching x-coordinates. Table columns have consistent x-offsets. Use the model-name row to define column positions, then assign data rows to the nearest column:

```python
# Define column centers from header row
col_centers = [s["x"] for s in header_row]
tolerance = 30  # px

# Assign data to columns
for data_span in data_row:
    # Find nearest column center
    dists = [abs(data_span["x"] - c) for c in col_centers]
    col_idx = dists.index(min(dists))
    if min(dists) < tolerance:
        table[col_idx].append(data_span["text"])
```

## When to Use This

- Raw `get_text()` produces garbled/mixed output for tables
- PDF has overlapping text layers (background + foreground)
- Tables span multiple rows where text positions tell the real structure
- Combine with custom font decoding (`references/custom-font-encoding.md`) when digits are also encoded

## Pitfalls

- Tolerance values (row grouping, column matching) may need tuning per document
- Some PDFs have non-rectangular layouts — verify column count across rows
- Text with large font size differences may have offset baselines
- Always spot-check 2-3 data points against the original PDF to confirm alignment
