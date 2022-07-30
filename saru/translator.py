import json
import logging
from json.decoder import JSONDecodeError
from urllib import request, parse
from urllib.error import URLError, HTTPError

deepl_error_message = "Translate via DeepL was unsuccessful."
_logger = logging.getLogger("saru")


def _parse(body):
    """Parse JSON from DeepL translation API, returns first translated string"""
    try:
        parsed = json.loads(body)
        return parsed["translations"][0]["text"]
    except JSONDecodeError:
        _logger.error(f"{deepl_error_message} Caught JSONDecodeError, bad JSON: {body}")
    except KeyError:
        _logger.error(f"{deepl_error_message} Caught KeyError, unexpected JSON: {body}")
    except IndexError:
        _logger.error(
            f"{deepl_error_message} Caught IndexError, unexpected JSON: {body}"
        )


def _fetch(text, url, key):
    """Makes HTTP POST request to DeepL translation API, returns JSON string"""
    data = parse.urlencode(
        {"auth_key": key, "text": text, "target_lang": "EN"}
    ).encode()
    req = request.Request(url, data=data)
    try:
        resp = request.urlopen(req)
    except HTTPError as e:
        _logger.error(f"{deepl_error_message} Response: HTTP {e.status}, {e.reason}")
    except URLError as e:
        _logger.error(f"{deepl_error_message} Caught URLError: {e.reason}")
    else:
        if resp.status != 200:
            _logger.error(
                f"{deepl_error_message} Response: HTTP {resp.status}, {resp.reason}"
            )
        return resp.read()


def translate(text, url, key):
    """Fetch from DeepL API and parse result, returns translated string"""
    json = _fetch(text, url, key)
    translation = _parse(json)
    return translation
