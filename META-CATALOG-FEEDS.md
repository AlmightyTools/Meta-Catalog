# Meta catalog feeds

Updated 2026-10-25. Catalog: The Almighty Tools® — Meta — Global (1039287162085046).

| Source | File | Generation |
| --- | --- | --- |
| US USD, 922783000838712 | meta-catalog-feed.xml | Hourly |
| 28 markets, 1067518952622184 | country-feed.csv | Daily |
| Spanish + French, 1321846853351634 | language-feed.csv | Daily |

Published files contain 122 unique numeric Shopify variant IDs from 71 parent products. These IDs are unchanged by the separate GMC identifier migration. Country overrides contain 3,416 rows (122 × 28). Language overrides contain 244 rows: 122 Spanish (`es_XX`) and 122 French (`fr_XX`), with the same IDs as the primary feed.

The language source is named **The Almighty Tools® — Meta — Languages ES + FR**. The existing public language-feed.csv URL and daily Meta download schedule are retained; no second catalog is needed. The language file overrides title and description. Prices, sale prices, stock and regional URLs remain in the independent country file. No language-and-country URL override is configured by this addition.

Markets: AE AR AT AU BE BR CA CH CL CO DE DK ES FI FR GB GR IE IL IT JP MX NL NO NZ PT SE SG. US uses the primary source. GB uses GBP; AU, CA and NZ use USD. Other currencies follow Shopify Markets. All product landing URLs use almighty.tools with variant and country context.

n8n workflows: dJKJKkPssEnXlVQM (primary), SR0H0Sa4E5y9YfoZ (country/language). Both generate independently from Shopify; neither reads the GMC XML files. French text comes from https://almighty.tools/data/feed-translations-fr.json independently of GMC. Missing French translations stop publication instead of silently creating a partial language file.

French generation execution 1386943 succeeded on October 25 at 21:50 America/New_York. Its one-time test trigger was removed and the ordinary daily schedule restored. Publication was verified separately from the Meta download; a successful generator run does not itself certify provider ingestion, event matching, or advertising eligibility.

The latest inspected main-source upload had zero upload failures and six Out of stock items. Stock was not overridden. The source's next scheduled upload remains the authority for ingestion of a later hourly file.

The retired workflow bp0yDn0lrh69OoOy remains stopped and archived. Four unused full-country-feed XML files were removed previously and are recoverable in Git history. Google, Axon and Microsoft retain their distinct feed purposes and identifier contracts.
