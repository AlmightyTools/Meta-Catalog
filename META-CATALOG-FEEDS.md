# Meta catalog feeds

Updated 2026-10-09. Catalog: The Almighty Tools® — Meta — Global (1039287162085046).

| Source | File | Schedule |
| --- | --- | --- |
| US USD, 922783000838712 | meta-catalog-feed.xml | Hourly generation and replacement |
| 28 markets, 1067518952622184 | country-feed.csv | Daily generation, download every 12 hours |
| Spanish, 1321846853351634 | language-feed.csv | Daily |

142 unchanged Shopify variant IDs. Country overrides have 3976 rows. Prices and sale prices come from Shopify Markets. Links use almighty.tools with variant, country and currency parameters.

Markets: AE AR AT AU BE BR CA CH CL CO DE DK ES FI FR GB GR IE IL IT JP MX NL NO NZ PT SE SG. US uses the primary source. GB uses GBP; AU and CA use USD. Other currencies follow Shopify Markets.

n8n: dJKJKkPssEnXlVQM (primary), SR0H0Sa4E5y9YfoZ (country/language). Production executions 1321430 and 1321427 succeeded. Meta country import on Oct 9 reported 4.0K updated, zero failed and zero issues.

Retired workflow bp0yDn0lrh69OoOy is stopped and archived. Four unused full-country-feed files (us, gb, ca-usd, au-usd) were removed and remain recoverable through Git history. Google generators remain separate.

Country completeness guard: current query allows 90 active products, 10 variants per product. Audit found 82 products, maximum 7 variants. Truncation rejects publication; implement pagination before limits are reached.

Landing checks: GB GBP, AU USD and CA USD matched. MX automated page checks returned 503/403 and remain unverified. Import success does not mean all products are eligible for advertising.

Final Meta verification: all three sources show All good. Main US source imported 142 variants on Oct 9 at 11:56 AM EDT; country source imported 3976 overrides (4.0K in UI), with zero failed and zero issues.
