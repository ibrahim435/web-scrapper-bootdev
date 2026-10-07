import unittest
from src.web_scrapper.crawl import (
    get_first_paragraph_from_html,
    get_heading_from_html,
    get_images_from_html,
    get_urls_from_html,
    normalize_url,
    extract_page_data,

)

class TestCrawl(unittest.TestCase):
    def test_normalize_url(self):
        input_url = "https://www.boot.dev/blog/path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html(self):
        input_body = "<html><body><h1>test title</h1><h2>test h2</h2></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "test title"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_h2_fallback(self):
        input_body = "<html><body><h2>test h2</h2></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "test h2"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_neither(self):
        input_body = "<html><body><p>No headings here.</p></body></html>"
        actual = get_heading_from_html(input_body)
        expected = ""
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_basic(self):
        input_body = "<html><body><p>First.</p><p>Second.</p></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        expected = "First."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_main_priority(self):
        input_body = """<html><body>
                <p>Outside paragraph.</p>
                <main>
                    <p>Main paragraph.</p>
                </main>
            </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_no_paragraph(self):
        input_body = "<html><body><h1>Only a heading</h1></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        expected = ""
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_main_without_paragraph(self):
        input_body = """<html><body>
                <main><h2>Heading only</h2></main>
                <p>Outside paragraph.</p>
            </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Outside paragraph."
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_relative(self):
        input_url = "https://blog.boot.dev"
        input_body = '<html><body><a href="/about">About</a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://blog.boot.dev/about"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_multiple(self):
        input_url = "https://blog.boot.dev"
        input_body = (
            "<html><body>"
            '<a href="/posts">Posts</a>'
            '<a href="https://google.com">Google</a>'
            '<a href="guides/python">Guides</a>'
            "</body></html>"
        )
        actual = get_urls_from_html(input_body, input_url)
        expected = [
            "https://blog.boot.dev/posts",
            "https://google.com",
            "https://blog.boot.dev/guides/python",
        ]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_no_links(self):
        input_url = "https://blog.boot.dev"
        input_body = "<html><body><a>No href here</a></body></html>"
        actual = get_urls_from_html(input_body, input_url)
        expected = []
        self.assertEqual(actual, expected)

    def test_get_images_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="https://example.com/pic.jpg" alt="Pic"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://example.com/pic.jpg"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_multiple(self):
        input_url = "https://crawler-test.com"
        input_body = (
            "<html><body>"
            '<img src="/a.png" alt="A">'
            '<img src="https://cdn.example.com/b.png" alt="B">'
            "</body></html>"
        )
        actual = get_images_from_html(input_body, input_url)
        expected = [
            "https://crawler-test.com/a.png",
            "https://cdn.example.com/b.png",
        ]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_missing_src(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img alt="missing src"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = []
        self.assertEqual(actual, expected)

    def test_extract_page_data_basic(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_relative_urls(self):
        input_url = "https://blog.boot.dev"
        input_body = """<html><body>
            <a href="/posts">Posts</a>
            <img src="/img/logo.png" alt="Logo">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://blog.boot.dev",
            "heading": "",
            "first_paragraph": "",
            "outgoing_links": ["https://blog.boot.dev/posts"],
            "image_urls": ["https://blog.boot.dev/img/logo.png"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_full_page(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h2>Fallback Heading</h2>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
                <a href="/inside">Inside link</a>
                <img src="/inside.png" alt="Inside">
            </main>
            <a href="/outside">Outside link</a>
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Fallback Heading",
            "first_paragraph": "Main paragraph.",
            "outgoing_links": [
                "https://crawler-test.com/inside",
                "https://crawler-test.com/outside",
            ],
            "image_urls": ["https://crawler-test.com/inside.png"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_empty_page(self):
        input_url = "https://crawler-test.com"
        input_body = "<html><body></body></html>"
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "",
            "first_paragraph": "",
            "outgoing_links": [],
            "image_urls": [],
        }
        self.assertEqual(actual, expected)
if __name__ == "__main__":
    unittest.main()
