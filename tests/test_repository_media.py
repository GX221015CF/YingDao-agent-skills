"""Media approval is exact-path and digest bound; normal privacy checks remain."""
from pathlib import Path
import json
import shutil
import tempfile
import unittest
from tools.check_repository import check

ROOT = Path(__file__).resolve().parents[1]


class MediaRepositoryTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "work").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "work")
        self.root = Path(self.temp.name)
        payload = json.loads((ROOT / "public-files.json").read_text(encoding="utf-8"))
        for rel in payload["files"]:
            dest = self.root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, dest)

    def tearDown(self):
        self.temp.cleanup()

    def codes(self):
        return {x["code"] for x in check(self.root)["issues"]}

    def test_reviewed_media_and_links_pass(self):
        self.assertTrue(check(self.root)["ok"])

    def test_changed_movie_bytes_rejected(self):
        p = self.root / "docs/media/yingdao-rpa-copilot-intro.mp4"
        p.write_bytes(p.read_bytes() + b"unexpected")
        self.assertIn("MEDIA_DIGEST_MISMATCH", self.codes())

    def test_extra_png_cannot_inherit_media_exception(self):
        p = self.root / "docs/media/unreviewed.png"
        p.write_bytes((self.root / "docs/media/yingdao-rpa-copilot-cover.png").read_bytes())
        manifest_path = self.root / "public-files.json"
        payload = json.loads(manifest_path.read_text())
        payload["files"].append("docs/media/unreviewed.png")
        manifest_path.write_text(json.dumps(payload), encoding="utf-8")
        self.assertIn("UNREVIEWED_BINARY_MEDIA", self.codes())

    def test_bad_media_manifest_and_duplicate_records_rejected(self):
        p = self.root / "docs/media/media-manifest.json"
        payload = json.loads(p.read_text())
        payload["files"][1] = payload["files"][0]
        p.write_text(json.dumps(payload), encoding="utf-8")
        self.assertIn("MEDIA_MANIFEST_INVALID", self.codes())

    def test_missing_movie_does_not_pass_as_existing_link(self):
        (self.root / "docs/media/yingdao-rpa-copilot-intro.mp4").unlink()
        codes = self.codes()
        self.assertIn("MISSING_OR_LINK", codes)
        self.assertIn("BROKEN_OR_EXTERNAL_LINK", codes)

    def test_media_manifest_does_not_disable_text_privacy_checks(self):
        p = self.root / "docs/media/README.md"
        p.write_text(p.read_text(encoding="utf-8") + "\n" + "C:" + "/Users/" + "PrivateExample/local" + "\n", encoding="utf-8")
        self.assertIn("PRIVATE_USER_PATH", self.codes())
