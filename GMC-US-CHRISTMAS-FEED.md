# US Christmas gift feed

Separate seasonal copy of the complete canonical US assortment. Existing feeds are unchanged.

- XML: `almighty-tools-gmc-us-dup.xml`
- Public URL: https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-us-dup.xml
- Canonical input: `almighty-tools-gmc-us.xml`
- Offer identity: `dup_US_{productId}_{variantId}`; group: `dup_US_{productId}`.
- Existing custom labels are preserved. Seasonal label 3: `christmas_gifts`; label 4: `dup`.
- For a separate Merchant Center source use country US, language English, feed label `US_CHRISTMAS`. The feed label is a data-source setting, not an XML attribute. This repository does not create a data source or launch a campaign.
- Ruler group filter: `dup_US_9346623570216`. The full assortment remains in the feed.

Titles start with the specification's exact “Gift for DIYer. ” followed by “Christmas Gift - ” and retain the entire canonical product name and variant. Descriptions introduce the Christmas gift use case, with category-aware wording, preserve all original product information, and end with the specification's exact “Ready to gift”. Tests require both exact phrases on every offer. AI-generated copy uses structured title/description with `trained_algorithmic_media`; no ordinary title/description fields override them. The requested gift wording does not establish a gift-wrapping service. No delivery date, discount or approval claims are added.

Run `python3 scripts/test_gmc_us_christmas.py` and `python3 scripts/build_gmc_us_christmas.py`. The workflow runs on canonical US changes or manual dispatch and publishes only this output. Push races rebase and regenerate from the latest source before retrying. Regeneration is event-driven; Google fetch/processing timing is independent. Invalid input fails without replacing the last valid file.

All prices, sale prices, stock, landing pages, photos, category, GTIN, brand and technical attributes are inherited unchanged. Tests verify offer-by-offer parity outside the explicitly changed fields and verify that source price/stock updates propagate. This does not resolve existing image-policy reviews; Google evaluates the new source separately. File publication is distinct from Merchant Center ingestion and ad activation.
