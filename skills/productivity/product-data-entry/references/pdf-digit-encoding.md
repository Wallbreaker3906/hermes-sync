# PDF Custom Font Digit Encoding

Some Chinese PDFs (especially product brochures from Chinese manufacturers) use custom fonts where digits 0-9 are mapped to Unicode Private Use Area (PUA) characters. This is common when the PDF embeds a custom font with non-standard glyph mapping.

## Common Mapping (倍豪船舶 pattern)

| Encoded Char | Unicode | Digit |
|:-----------:|:-------:|:-----:|
|  | U+F6B1 | 0 |
|  | U+F6B2 | 1 |
|  | U+F6B3 | 2 |
|  | U+F6B4 | 3 |
|  | U+F6B5 | 4 |
|  | U+F6B6 | 5 |
|  | U+F6B7 | 6 |
|  | U+F6B8 | 7 |
|  | U+F6B9 | 8 |
|  | U+F6BA | 9 |

## Python Decoder

```python
import pymupdf

DECODE = {chr(0xF6B1 + i): str(i) for i in range(10)}

def decode_digits(text):
    for k, v in DECODE.items():
        text = text.replace(k, v)
    return text

doc = pymupdf.open("brochure.pdf")
text = decode_digits(page.get_text())
```

## Verification

Always verify the mapping by decoding known values:
- Page footer numbers (pages are typically numbered with these encoded digits)
- Known years or model numbers that appear in both encoded and unencoded text
- Cross-reference with English text on the same page (e.g., "12000KW" in English vs encoded "12000KW" in Chinese)

## Other Possible Mappings

Different PDF generators may use different PUA ranges. If the above mapping doesn't work:
1. Check if decoded values make sense against known ranges
2. Look for English text on the same page to cross-reference
3. The offset pattern (consecutive U+F6Bx = digits 0-9) is common but the base address may differ
