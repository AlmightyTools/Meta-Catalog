"""Bounded retry for read-only Shopify catalog requests."""

import json
import math
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def read_json(request, *, timeout):
    for attempt in range(3):
        delay = 2 ** (attempt + 1)
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in {429, 502, 503, 504} or attempt == 2:
                raise
            retry_after = error.headers.get('Retry-After')
            if retry_after:
                try:
                    delay = float(retry_after)
                except ValueError:
                    try:
                        delay = (parsedate_to_datetime(retry_after) -
                                 datetime.now(timezone.utc)).total_seconds()
                    except (ValueError, TypeError, OverflowError):
                        pass
            if not math.isfinite(delay) or delay > 60:
                raise
        except (TimeoutError, URLError) as error:
            if attempt == 2 or isinstance(error, URLError) and not isinstance(error.reason, TimeoutError):
                raise
        time.sleep(max(delay, 2))
