# Lints the visible copy of a page against the owner's word rules: for each HTML
# path given, the text between <main and </main> (tags stripped, entities
# decoded) goes through `python D:/privacy/scripts/campaign/campaign.py lint`.
# Only <main> is checked because the shared header carries "SWM price on Base",
# which the lint would flag on every page. A path that is not HTML (no <main>)
# is linted whole. Exit code 1 if any file has a lint error.
#   python tools/lint_main.py token/index.html get-swm/index.html
import html
import os
import re
import subprocess
import sys
import tempfile

CAMPAIGN = "D:/privacy/scripts/campaign/campaign.py"


def main_text(source):
    if "<main" in source and "</main>" in source:
        source = source[source.index("<main"):source.index("</main>")]
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    source = re.sub(r"<[^>]+>", " ", source)
    return re.sub(r"\s+", " ", html.unescape(source)).strip() + "\n"


failed = False
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as f:
        text = main_text(f.read())
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as tmp:
        tmp.write(text)
    try:
        run = subprocess.run([sys.executable, CAMPAIGN, "lint", tmp.name],
                             capture_output=True, text=True, encoding="utf-8")
    finally:
        os.unlink(tmp.name)
    print(path + ": " + (run.stdout.strip().split(": ", 1)[-1] if run.stdout else run.stderr.strip()))
    if run.returncode != 0:
        failed = True
sys.exit(1 if failed else 0)
