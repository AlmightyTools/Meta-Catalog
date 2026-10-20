# The Almighty Tools® — Axon US catalog

Public CSV: https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-axon-us.csv

The existing US Merchant feed is the upstream source. It already applies the approved active-product, US-market, service-add-on, mystery-gift, and duplicate-card exclusions. This is a US/USD catalog; do not use it to advertise GBP/EUR prices.

- `itemId` is the numeric Shopify product ID and `id` the numeric variant ID, preserving the IDs of the previous Shopify-connected Axon catalog. Google-specific `shopify_US_...` prefixes are not exported.
- All landing links use `almighty.tools`, explicit variants, and `country=US`. Existing query parameters remain intact; no fixed advertising UTM is added.
- `price` is the current payable USD price, including an existing source sale price. No sale dates are invented and no artificial crossed-out price is exported.
- Approved primary image bytes are mirrored as immutable content-addressed JPG/PNG files because Axon documents these formats. Original JPG/PNG bytes are preserved, including provenance metadata. Other raster formats are converted without visual edits.
- No review count/rating is exported: these are not required for this catalog.
- Workflow `Refresh Axon US catalog` runs after upstream US feed changes, manually, and daily at 17:15 UTC before Axon's configured 18:00 UTC pull. Upstream prices/stock still originate in the existing daily n8n US generator.
- A malformed identity, wrong domain/currency/variant, failed image, invalid price, fewer than 80 variants, or an over-20% count drop stops publication and retains the prior feed. Review the failed Actions run rather than bypassing the guard automatically.
- Never disconnect the Shopify pixel app merely to replace the catalog source. Catalog-source changes and conversion tracking are separate.

Verification of successful generation does not prove Axon's import or campaign approval. Confirm the catalog manager's final sync status, count, prices, links, and sample variant IDs after a source change.

Specification: https://support-preview.axon.ai/en/growth/promoting-your-websites/dynamic-catalog/dynamic-product-catalog
