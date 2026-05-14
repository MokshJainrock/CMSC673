
# usage: python -m src.clean <html_folder> <out_jsonl> "<book name>"

import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup


JUNK_TAGS = ["nav", "header", "footer", "script", "style", "figure","table", "aside", "form", "iframe", "noscript"]

JUNK_CLASS = re.compile(r"(figure|caption|nav|sidebar|toc|footer|header|"
    r"learning-objectives|key-terms|chapter-objectives|"
    r"summary|review-questions)", re.I)

MIN_TOKENS = 50


def strip_junk(soup):
    for tag in soup.find_all(JUNK_TAGS):
        tag.decompose()
    for tag in soup.find_all(attrs={"class": JUNK_CLASS}):
        tag.decompose()
    for tag in soup.find_all(attrs={"id": JUNK_CLASS}):
        tag.decompose()
    return soup


def split_sections(soup):
    sections = []
    title = None
    body = []
    for el in soup.find_all(["h2", "h3", "p", "li"]):
        if el.name == "h2" or el.name == "h3":
            if title and body:
                sections.append((title, " ".join(body)))
            title = el.get_text(" ", strip=True)
            body = []
        else:
            text = el.get_text(" ", strip=True)
            if text:
                body.append(text)
    if title and body:
        sections.append((title, " ".join(body)))
    return sections


def normalize_whitespace(text):
    text = text.replace("\xa0", " ").replace("​", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_garbage(text):
    if not text:
        return True
    words = text.split()
    if len(words) < MIN_TOKENS:
        return True
    digits = 0
    for w in words:
        if w.isdigit():
            digits += 1
    if digits / len(words) > 0.5:
        return True
    return False


def build(folder, out_path, book_name):
    folder = Path(folder)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with open(out_path, "w") as out:
        for html_file in sorted(folder.glob("*.html")):
            soup = BeautifulSoup(html_file.read_text(), "html.parser")
            soup = strip_junk(soup)
            chapter_id = html_file.stem
            i = 0
            for title, body in split_sections(soup):
                body = normalize_whitespace(body)
                if is_garbage(body):
                    i += 1
                    continue
                doc = {
                    "id": f"{chapter_id}-{i}",
                    "title": title,
                    "source": book_name,
                    "chapter": chapter_id,
                    "section": str(i),
                    "text": body,
                }
                out.write(json.dumps(doc) + "\n")
                written += 1
                i += 1

    print(f"wrote {written} sections to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print('usage: python -m src.clean <html_folder> <out_jsonl> "<book name>"')
        sys.exit(1)
    build(sys.argv[1], sys.argv[2], sys.argv[3])
