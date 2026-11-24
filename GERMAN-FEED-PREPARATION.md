# German product feed preparation — November 24, 2026

**Prepared only. No provider source, schedule, catalog or live feed was changed.**

The existing Google, Meta and OpenAI generators remain active. The isolated
preparation script consumes their current canonical product identities and
public contextual prices without replacing their outputs. German activation
must follow the separately managed storefront index release and the gates below.

## Exact initial source plan

| Channel | Staged output | Language / country / currency | Treatment |
| --- | --- | --- | --- |
| Google | `almighty-tools-gmc-de-de.xml` | de / DE / EUR | New language source; preserve current English DE source and IDs |
| Google | `almighty-tools-gmc-at-de.xml` | de / AT / EUR | New language source; preserve current English AT source and IDs |
| Google | `almighty-tools-gmc-ch-de.xml` | de / CH / EUR | New language source; Shopify-backed market uses EUR, not invented CHF conversion |
| Meta | `meta-language-de-candidate.csv` | de_XX / existing global catalog | Candidate secondary language source, same numeric variant IDs; preserve existing ES/FR and country sources |
| Meta | `meta-language-country-de-candidate.csv` | de_XX combined with DE/AT/CH | URL-only candidate; preserve commercial country attributes |
| OpenAI | `almighty-tools-chatgpt-german-candidate.csv` | Existing all-market CSV; de rows only for DE/AT/CH | Replacement candidate for the existing single hosted catalog, not a second overlapping upload |
| Microsoft | `microsoft-ads-{de,at,ch}-de.xml` | de / DE, AT, CH / EUR | Three optional target-specific candidates, numeric variant IDs; merchant catalog targeting must be verified first |

DE/AT/CH are the initial German-market scope already selected by the existing
OpenAI locale map. This does not automatically switch other selling countries
to German. Google supports German data for other supported target countries,
but any expansion must validate that country's language, currency and checkout.

The independent Axon export is explicitly US/USD; it must not be repurposed as
a EUR German catalog. No additional German Axon catalog/target is confirmed.
The reviews export is not a product-offer catalog and is not translated or
duplicated here. Google Ads consumes Merchant Center rather than a separate
product feed. Existing AU/NZ campaign compatibility and US Christmas feeds keep
their purpose, IDs and language.

## Verified public evidence

- 74 German product routes return HTTP 200 and `lang=de`. All 74 still return
  `noindex, follow` in the audited snapshot; each primary image returns 200.
- Current DE/AT/CH canonical exports contain 70 products / 121 offers each.
  210 public market-product API reads verified exact variant identities,
  current/compare-at prices, EUR and stock. Each staged catalog retains the
  eight genuinely out-of-stock offers; no availability is forced in stock.
- Four German routes are outside the current European canonical export:
  replacement screw kit, the DIYers bundle, the DIYers essentials bundle and
  Steam Cleaner. Existing exclusions are preserved rather than silently
  expanding the product set. Steam is specifically excluded until real regional
  purchase availability and the correct hardware variant are confirmed.
- 85 of 121 variant photos have an exact original-image match to the reviewed
  German artwork mapping. Those German images are staged only. The remaining
  36 variants retain their existing approved primary photos; they are not
  silently assigned a product-level image of an unverified color/model.
- Existing ES/FR Meta rows and country stock/price data remain unchanged.
  Existing non-DE/AT/CH OpenAI records remain exactly equal. All 49 root live
  product XML/CSV files remain byte-identical in the checkout.

## Activation gates and observed blockers

1. Independently verify the actual production German index release; preparation
   is not permission to remove robots tags or publish the storefront.
2. Fix or independently resolve market-context behavior. The public German
   Ruler HTML/JSON-LD returned **USD** for explicit DE, AT and CH URLs with
   `currency=EUR` and exact variant 48877287047464. The corresponding market API
   returns EUR. This is an observed initial-HTML discrepancy, not a claim that
   checkout itself charges USD. German feed, visible price, currency, selected
   variant and checkout language must be checked together before registration.
3. Review localized primary images under each channel's image policy. A source
   translation mapping or HTTP 200 is not Google/Meta image approval. Finish
   the exact localized image mapping for the remaining variants.
4. Meta documents combined language/country precedence above language and country
   overlays. A separate `meta-language-country-de-candidate.csv` stages 363 URL-only
   rows (`id,override,url`, e.g. `de_XX|DE`) with exact country, currency and variant.
   Registering LANGUAGE_AND_COUNTRY requires API setup; nothing is registered here.
   Keep price/availability exclusively in the country feed. Provider readback is
   still required: authenticated Commerce Manager showed variant 48877287047464
   with Austria selected but US/USD price and US link; its country coverage table
   showed AR/CL/CO/MX only despite the country source reporting 3.4K successful rows
   and zero issues. Do not treat successful upload as effective country coverage.
   Existing language rows have no URL field (1830 European country rows use English
   paths; 122 use Spanish). This is a verified discrepancy requiring investigation,
   not permission to replace or re-register a live source.
5. Verify current Microsoft Merchant Center catalogs, supported target markets
   and effective currency before enabling those optional sources. No campaign,
   budget or import setting was changed.

There was no provider import, ad launch, image-policy approval or new Business
Hub processing acknowledgment in this preparation.

## Reproduce preparation

Use a sanitized evidence directory containing `german-pages.json`,
`market-quotes.json`, `exact-localized-variant-images.json` and
`collection-proof.json`. These contain public product data only; never include
customer records, tokens or raw page exports.

```sh
python3 scripts/prepare_german_feeds.py --evidence /absolute/evidence --output /absolute/candidates
python3 scripts/test_prepare_german_feeds.py
```

The output directory must be outside this checkout. The script is not wired
to Actions or n8n, cannot register sources, and always records
`activation_ready=false`. Candidate prices come from exact contextual variants,
not currency relabeling or guessed exchange rates. Refresh evidence and rerun
before any later authorized activation.

## Primary channel references

- [Google supported languages and currencies](https://support.google.com/merchants/answer/160637?hl=en)
- [Google consistent feed, landing and checkout language](https://support.google.com/merchants/answer/10248086?hl=en)
- [Meta localized feeds, combined URL schema and precedence](https://developers.facebook.com/documentation/ads-commerce/catalog/localized-catalog/localized-catalog-setup)
- [OpenAI product-feed specification](https://developers.openai.com/commerce/specs/file-upload/products)
- [Microsoft product identity and currency](https://learn.microsoft.com/en-us/advertising/shopping-content/products-resource)
