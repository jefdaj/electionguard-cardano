import re
from pathlib import Path

MARKER = re.compile(r"<!--\s*compose-docs\s+(\S+)\s*-->")
START, END = "# ---md", "# ---"

def extract(path):
    out, inside = [], False
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        if s == START:
            inside = True
            continue
        if s == END and inside:
            inside = False
            out.append("")  # blank line between blocks
            continue
        if inside:
            text = line.lstrip()
            if text.startswith("#"):
                text = text[1:].removeprefix(" ")
            out.append(text)
    return "\n".join(out).strip() + "\n"

def on_page_markdown(markdown, page, config, files):
    return MARKER.sub(lambda m: extract(m.group(1)), markdown)

