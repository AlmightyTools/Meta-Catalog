"""Bounded, rate-limit-aware reads of existing public Shopify data."""
import email.utils
import datetime
import http.client
import json
import time
import urllib.error
import urllib.request


def retry_delay(value, attempt):
    minimum = 5 * (2 ** attempt)
    if value:
        try:
            requested = float(value)
        except ValueError:
            date = email.utils.parsedate_to_datetime(value)
            requested = (date - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        if requested > 120:
            raise RuntimeError('Provider Retry-After exceeds this bounded refresh window')
        minimum = max(minimum, requested)
    return max(0, minimum)


def read_json(request, timeout=30, *, opener=None, sleep=None):
    opener = opener or urllib.request.urlopen
    sleep = sleep or time.sleep
    for attempt in range(4):
        try:
            with opener(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in (429, 502, 503, 504) or attempt == 3:
                error.close()
                raise
            try:
                delay = retry_delay(error.headers.get('Retry-After'), attempt)
            finally:
                error.close()
        except (TimeoutError, urllib.error.URLError, http.client.RemoteDisconnected):
            if attempt == 3:
                raise
            delay = retry_delay(None, attempt)
        print('Public data temporarily unavailable; respecting bounded retry delay', flush=True)
        sleep(delay)
