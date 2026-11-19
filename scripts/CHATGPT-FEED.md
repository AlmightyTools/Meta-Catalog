# ChatGPT product discovery catalog

The hosted `almighty-tools-chatgpt.csv` follows the OpenAI native product-feed
schema. It is separate from Google/Meta campaign feeds. Source prices, product
copy and images from the 29 canonical country GMC files remain unchanged.

Active Shopify markets and 11 enabled currencies were read from Shopify Admin on
2026-11-19. The explicit `chatgpt-markets.json` maps 30 actual selling countries to
their effective currency, including USD for AU/CA/NZ/BR/AE and QAR for QA.
If Shopify markets change, verify and update this mapping and Business Hub settings.

Qatar has no existing canonical GMC file. Its OpenAI-only XML source is refreshed
from the same tokenless contextual Storefront API as the public website. Products
not published to that market are omitted. On initial setup, 121 public contextual
variant prices and availability flags matched independent Shopify Admin readback;
the US-only Steam Cleaner was not exposed in the Qatar storefront.

IDs and variant groups are country-qualified to avoid cross-market overwrites.
Google campaign/Christmas alias IDs are never imported. Variant names/values are
refreshed from public Shopify product definitions, not inferred from ad titles.

The workflow refreshes after canonical/image updates and every six hours. It
publishes only the OpenAI catalog and its public-data caches. All validation and
source refreshes must succeed before replacement; no Shopify credentials are used.
This refresh schedule does not guarantee the timing of Business Hub processing.

Run:
```sh
python3 scripts/refresh_chatgpt_variant_options.py
python3 scripts/refresh_chatgpt_qatar.py
python3 scripts/build_chatgpt_feed.py
python3 scripts/test_chatgpt_feed.py
```

Reference: https://developers.openai.com/commerce/specs/file-upload/products
Search eligibility is enabled; advertising eligibility is explicitly disabled.
An accepted feed is not proof of product display in a ChatGPT response.
