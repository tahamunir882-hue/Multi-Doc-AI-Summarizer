def chunk_text(text: str, max_chars: int = 6000) -> list[str]:
    """Split on paragraphs, keeping each chunk under max_chars."""
    text = text.replace("\f", "\n")      # \f marks page breaks
    chunks, cur = [], ""
    for para in text.split("\n"):
        while len(para) > max_chars:          # very long single paragraph
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(para[:max_chars])
            para = para[max_chars:]
        if len(cur) + len(para) + 1 > max_chars and cur:
            chunks.append(cur)
            cur = ""
        cur += para + "\n"
    if cur.strip():
        chunks.append(cur)
    return chunks
