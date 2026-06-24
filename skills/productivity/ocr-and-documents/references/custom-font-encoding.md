# Custom Font-Encoded Digits in PDFs

## Problem

When a PDF uses custom/embedded fonts (common in Chinese corporate brochures), `pymupdf.get_text()` may return digits as Private Use Area (PUA) Unicode characters (U+F000–U+FFFF range). This makes numbers unreadable — e.g., "12000KW" becomes "KW".

## Detection

Scan extracted text for characters with `ord(ch) >= 0xF000`:

```python
for ch in text:
    if ord(ch) >= 0xF000:
        print(f"U+{ord(ch):04X} = {ch}")
```

## Decoding

1. **Identify the mapping** by matching known values. Look for verifiable numbers in the text (years, percentages, known model ranges) and reverse-engineer:

   ```
   "超过 %" → should be "超过 50%" → =5, =0
   "BP-C" → should be "BP-150C" → =1, =5, =0
   ```

2. **Build decode map**. Common pattern: consecutive PUA codepoints map to 0-9 sequentially:

   ```python
   # Example: U+F6B1 = '0', U+F6B2 = '1', ..., U+F6BA = '9'
   DECODE = {chr(0xF6B1 + i): str(i) for i in range(10)}

   def decode_numbers(text):
       for k, v in DECODE.items():
           text = text.replace(k, v)
       return text
   ```

3. **Verify**: After decoding, spot-check a few known values to confirm correctness.

## Pitfalls

- Not all PUA characters are digits — verify the mapping before applying globally.
- Some PDFs may have non-contiguous mappings; always verify at least 3 known values.
- The encoding may vary between different PDFs from different sources.
