"""Local smoke checks for the published static pages; no network required."""

from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "donna/index.html", "donna/privacy.html")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.links, self.declarations = set(), [], []
        self.title, self.in_title = [], False

    def handle_decl(self, value):
        self.declarations.append(value.lower())

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag)
        self.in_title = self.in_title or tag == "title"
        self.links.extend(value for key, value in attrs if key in {"href", "src"} and value)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


class StaticSiteTests(unittest.TestCase):
    def test_landing_and_donna_pages_have_content_and_resolvable_local_links(self):
        for name in PAGES:
            with self.subTest(page=name):
                path = ROOT / name
                page = Page()
                page.feed(path.read_text(encoding="utf-8"))
                page.close()
                self.assertIn("doctype html", page.declarations)
                self.assertTrue({"html", "head", "title", "body"} <= page.tags)
                self.assertTrue("".join(page.title).strip(), "Page needs a title")
                for link in page.links:
                    url = urlsplit(link)
                    if url.scheme or url.netloc or not url.path:
                        continue
                    local = unquote(url.path)
                    target = ((ROOT / local.lstrip("/")) if local.startswith("/") else path.parent / local).resolve()
                    self.assertTrue(target.is_relative_to(ROOT), f"Link leaves the published site: {link}")
                    if target.is_dir():
                        target /= "index.html"
                    self.assertTrue(target.is_file(), f"Missing local link: {name} -> {link}")


if __name__ == "__main__":
    unittest.main()
