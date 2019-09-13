import re
import requests
from bs4 import BeautifulSoup
from flask import Request, Response


HABRA_HOST = 'https://habr.com/'
REQUEST_HEADERS_EXCLUDE = ['host', ]
RESPONSE_HEADERS_EXCLUDE = [
    'content-encoding', 'content-length', 'transfer-encoding', 'connection',
]
NON_TEXT_HTML_TAGS = ['style', 'script', '[document]', 'head', 'title', ]


class HabraRetriever:
    def __init__(self, request: Request):
        self._request = request
        self._url = request.url.replace(request.host_url, HABRA_HOST)


def process_proxy(request: Request) -> Response:
    url = request.url.replace(request.host_url, HABRA_HOST)
    headers = {
        k: v for k, v in request.headers
        if k.lower() not in REQUEST_HEADERS_EXCLUDE
    }
    habra_resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies
    )
    headers = [
        (key, habra_resp.raw.headers[key]) for key in habra_resp.raw.headers
        if key.lower() not in RESPONSE_HEADERS_EXCLUDE
    ]
    # modify content only for text/html response
    if habra_resp.raw.headers.get('Content-Type', '').startswith('text/html'):
        processed_content = _modify_habra_content(
            habra_resp.text, request.host_url
        )
        return Response(processed_content, habra_resp.status_code, headers)
    else:
        return Response(habra_resp.content, habra_resp.status_code, headers)


def _modify_habra_content(content: str, host_url: str) -> str:
    soup = BeautifulSoup(content, 'html5lib')
    _process_words(soup)
    _process_links(soup, host_url)
    return str(soup)


def _process_words(soup: BeautifulSoup) -> None:
    def visible_and_matchable(_element):
        if _element.parent.name in NON_TEXT_HTML_TAGS:
            return False
        elif re.match('<!--.*-->', str(_element.encode('utf-8'))):
            return False
        elif len(_element.string) < word_length:
            return False
        elif not words_to_change_re.search(_element.string):
            return False
        return True

    def tm_appender(match_obj):
        return '{0}{1}'.format(match_obj.group(), '\u2122')

    word_length = 6
    words_to_change_re = re.compile(r'\b(\w{%s})\b' % word_length)

    text_elements = soup.findAll(text=True)
    visible_elements = filter(visible_and_matchable, text_elements)
    for element in visible_elements:
        txt = str(element.string)
        new_txt = words_to_change_re.sub(tm_appender, txt)
        element.string.replace_with(new_txt)


def _process_links(soup: BeautifulSoup, host_url: str) -> None:
    for element in soup.find_all('a'):
        if 'href' not in element.attrs:
            continue
        href = str(element['href'])
        if href.startswith(HABRA_HOST):
            element['href'] = href.replace(HABRA_HOST, host_url)
    for element in soup.find_all('use'):
        if 'xlink:href' not in element.attrs:
            continue
        href = str(element['xlink:href'])
        if href.startswith(HABRA_HOST):
            element['xlink:href'] = href.replace(HABRA_HOST, host_url)
