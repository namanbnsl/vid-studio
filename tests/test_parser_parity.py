"""The preview and renderer must agree on scene content and duration."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills/vid-studio/scripts"))
import studio


@unittest.skipUnless(shutil.which("node"), "Node is needed to check the browser parser")
class ParserParityTest(unittest.TestCase):
    def test_preview_matches_export(self):
        ui = (REPO / "skills/vid-studio/assets/ui/index.html").read_text()
        parser = ui[ui.index("const SCENE_TYPES ="):ui.index("// One preview at a time:")]
        cases = [p.read_text() for p in sorted((studio.ASSETS / "examples").glob("*.md"))]
        cases += [
            "No beats", "## Blank", "## Hook\nVisual:\nNote:",
            "  ## **Hook** #\n### Ignore this heading\nHi there\nVisual: text",
            "## Hook\n[3](https://example.com) [1—3] ![chart]() [label]()\nVisual: text",
            "## Hook\n* __Visual__: bars | Limits | : 42 | Foo: bar: ₹3.2 lakh | Missing:\n__Text__: OK",
            "## Hook\n- Voiceover words\n*Voiceover*\n**Note:** Check source\nVisual: unknown | all fields",
            "## Hindi\nयह है नया नियम । [1, 2] [1–3]\nVisual: compare | Cap | Old: ₹500 | Now: ₹1,000",
            "## Timeline\r\nVisual: timeline | Dates | 2024: First: launch | : blank\r\n## End\r\nBye",
            "## Photo\nWords.\nImage: media/a.jpg | Photo: A | extra\n**Source:** RBI\nDuration: 3.25 S\n## Bare\nImage:\nSource:\nDuration: 0\n## Big\nDuration: 99s\nVisual: image | Tap | media/t.png | Photo: B",
            "## Card\nImage: media/a.jpg | Photo: A / Flickr, CC BY 2.0 | full\n## Only\nImage: media/b.jpg|TOP\n## Piped\nImage: media/c.jpg | A | B | top",
            "## Call\nVisual: message | Unknown number | Sir, refund ready hai | you: कौन? | बस approve कर दीजिए\nText: Example",
        ]
        inputs = [{"text": text, "wpm": wpm} for text in cases for wpm in (80, 160, 175, 260)]
        program = parser + "\nconst fs=require('node:fs');process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(x=>parseScenes(x.text,x.wpm))));"
        result = subprocess.run(["node", "-e", program], input=json.dumps(inputs), text=True, capture_output=True, check=True)
        for case, preview in zip(inputs, json.loads(result.stdout)):
            with self.subTest(text=case["text"], wpm=case["wpm"]):
                self.assertEqual(studio.parse_scenes(case["text"], case["wpm"]), preview)


if __name__ == "__main__":
    unittest.main()
