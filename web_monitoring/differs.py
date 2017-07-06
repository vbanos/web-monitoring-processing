from bs4 import BeautifulSoup
import diff_match_patch
import re
import web_monitoring.pagefreezer
import sys


# BeautifulSoup can sometimes exceed the default Python recursion limit (1000).
sys.setrecursionlimit(10000)


def compare_length(a_body, b_body):
    "Compute difference in response body lengths. (Does not compare contents.)"
    return len(b_body) - len(a_body)


def identical_bytes(a_body, b_body):
    "Compute whether response bodies are exactly identical."
    return a_body == b_body


def _get_text(html):
    "Extract textual content from HTML."
    soup = BeautifulSoup(html, 'html.parser')
    return soup.findAll(text=True)


def _is_visible(element):
    "A best-effort guess at whether an HTML element is visible on the page."
    # adapted from https://www.quora.com/How-can-I-extract-only-text-data-from-HTML-pages
    INVISIBLE_TAGS = ('style', 'script', '[document]', 'head', 'title')
    if element.parent.name in INVISIBLE_TAGS:
        return False
    elif re.match('<!--.*-->', str(element.encode('utf-8'))):
        return False
    return True


def _get_visible_text(html):
    return list(filter(_is_visible, _get_text(html)))


def side_by_side_text(a_text, b_text):
    "Extract the visible text from both response bodies."
    return {'a_text': _get_visible_text(a_text),
            'b_text': _get_visible_text(b_text)}


def pagefreezer(a_url, b_url):
    "Dispatch to PageFreezer."
    # Just send PF the urls, not the whole body.
    # It is still useful that we downloaded the body because we are able to
    # validate it against the expected hash.
    return web_monitoring.pagefreezer.compare(a_url, b_url)


def pagefreezer_direct(a_text, b_text):
    "Dispatch to PageFreezer, the slow way."
    # Send PF the full body.
    return web_monitoring.pagefreezer.compare(a_text, b_text)


d = diff_match_patch.diff_match_patch()

def _diff(a_text, b_text):
    return d.diff_compute(a_text, b_text, False, DEADLINE)


def html_text_diff(a_text, b_text):
    """
    Example
    ------
    >>> text_diff('<p>Deleted</p><p>Unchanged</p>',
    ...           '<p>Added</p><p>Unchanged</p>')
    [(0, '<p>'), (-1, 'Delet'), (1, 'Add'), (0, 'ed</p><p>Unchanged</p>')]
    """
    t1 = ' '.join(_get_visible_text(a_text))
    t2 = ' '.join(_get_visible_text(b_text))
    DEADLINE = 2  # seconds
    return d.diff_compute(t1, t2, checklines=False, deadline=DEADLINE)


def html_source_diff(a_text, b_text):
    """
    Example
    ------
    >>> text_diff('<p>Deleted</p><p>Unchanged</p>',
    ...           '<p>Added</p><p>Unchanged</p>')
    [(-1, '<p>Deleted</p>'), (1, '<p>Added</p>'), (0, '<p>Unchanged</p>')]
    """
    DEADLINE = 2  # seconds
    return d.diff_compute(a_text, b_text, checklines=False, deadline=DEADLINE)
