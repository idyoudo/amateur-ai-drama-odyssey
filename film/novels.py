"""小说 TXT 导入：编码识别、章节/字数/作者/标题解析。"""
import codecs
import re

CJK_RE = re.compile(r"[一-鿿]")
CHAPTER_RE = re.compile(
    r"^\s*(?:第[0-9零〇一二三四五六七八九十百千万两]+[章回节卷部集][^\n]{0,40}"
    r"|Chapter\s+\d+[^\n]{0,60}"
    r"|\d{1,4}[、.．]\s*\S[^\n]{0,38})\s*$",
    re.I | re.M,
)
AUTHOR_RE = re.compile(r"(?:作\s*者|Author)\s*[:：]\s*(.+)")


def decode_bytes(data):
    """按常见中文编码依次尝试；返回 (text, encoding)。"""
    if data.startswith(codecs.BOM_UTF16_LE) or data.startswith(codecs.BOM_UTF16_BE):
        try:
            return data.decode("utf-16"), "utf-16"
        except UnicodeDecodeError:
            pass
    for enc in ("utf-8-sig", "gb18030"):
        try:
            text = data.decode(enc)
            if "�" not in text:
                return text, enc.replace("-sig", "")
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8(replace)"


def _filename_title(filename):
    name = (filename or "未命名小说").rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return re.sub(r"\.txt$", "", name, flags=re.I)[:80] or "未命名小说"


def parse_novel(text, filename=""):
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.splitlines()
    nonempty = [(i, ln.strip()) for i, ln in enumerate(lines) if ln.strip()]
    chapter_titles = [m.group(0).strip() for m in CHAPTER_RE.finditer(text)]

    title = ""
    for _, ln in nonempty[:3]:
        if AUTHOR_RE.search(ln):
            continue
        if CHAPTER_RE.match(ln):
            break
        if 1 <= len(ln) <= 40:
            title = ln.strip("《》 \t")
            break
    title = title or _filename_title(filename)

    author = ""
    for _, ln in nonempty[:40]:
        m = AUTHOR_RE.search(ln)
        if m:
            author = m.group(1).strip()[:60]
            break

    char_count = len(CJK_RE.findall(text))
    if char_count < 50:  # 英文/拼音文本按词计数
        char_count = len(re.findall(r"[A-Za-z0-9']+", text))
    words_wan = round(char_count / 10000.0, 1)

    logline = ""
    first_chapter = CHAPTER_RE.search(text)
    body = text[first_chapter.end():] if first_chapter else text
    for para in re.split(r"\n\s*\n", body):
        p = " ".join(para.split())
        if not p or p == title or AUTHOR_RE.search(p) or CHAPTER_RE.match(p):
            continue
        if len(p) >= 20:
            logline = p[:120]
            break

    start = 0
    if first_chapter:
        start = first_chapter.end()
    excerpt = " ".join(text[start:start + 400].split())[:300]

    return {
        "title": title,
        "author": author,
        "chapters": max(1, len(chapter_titles)),
        "chapter_titles": chapter_titles[:200],
        "char_count": char_count,
        "words_wan": words_wan,
        "logline": logline,
        "excerpt": excerpt,
    }
