# Almighty Tools Google Merchant country feeds

Updated: 2026-10-08 UTC.

These are owned Google Merchant XML files. Meta catalog feeds are unchanged. Shopify/agency integrations have not been disabled.

## Readiness

- US English: existing daily workflow `YpAkJgKt9UmShjiL`, 05:10 UTC.
- International files: initial Shopify MCP snapshots generated and validated for 29 country/language pairs.
- International daily workflow: `y4JecM16QSlVln38`, planned 05:25 UTC. Currently unpublished: the existing Shopify credential requires `read_publications` before safe automatic execution.
- Files are not a confirmation of approval or serving in Merchant Center. Register/validate replacement sources and check shipping/campaign feed labels before cutting over.

## Content rules

Use active products published in the country; exclude `no-feed` products (screw kit, processing, shipping insurance and mystery gifts). Include regional FR/LATAM cards only for the matching language. Prices and comparison prices come directly from Shopify contextualPricing. Availability comes from Shopify. Existing real clean product photos are reused by variant, product and SKU, including regional duplicates. No generated product art. Preserve branded names, use existing translations for descriptions. Untranslated new products receive a short localized product label instead of invented claims.

Country-specific landing pages use the Shopify checkout storefront, localized routes and explicit country/currency parameters. The primary US English file retains its existing landing route.

## Feed URLs

Use **Raw** URLs, not GitHub blob page URLs.

| Country | Language | Currency | Products | Offers | Feed |
|---|---|---|---:|---:|---|
| United States | en | USD | 76 | 142 | [almighty-tools-gmc-us.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-us.xml) |
| United Arab Emirates | en | USD | 76 | 142 | [almighty-tools-gmc-ae.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-ae.xml) |
| Argentina | es | ARS | 90 | 154 | [almighty-tools-gmc-ar.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-ar.xml) |
| Austria | en | EUR | 76 | 142 | [almighty-tools-gmc-at.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-at.xml) |
| Australia | en | USD | 76 | 142 | [almighty-tools-gmc-au.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-au.xml) |
| Belgium | en | EUR | 76 | 142 | [almighty-tools-gmc-be.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-be.xml) |
| Brazil | en | USD | 76 | 142 | [almighty-tools-gmc-br.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-br.xml) |
| Canada | en | USD | 76 | 142 | [almighty-tools-gmc-ca.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-ca.xml) |
| Switzerland | en | EUR | 76 | 142 | [almighty-tools-gmc-ch.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-ch.xml) |
| Chile | es | CLP | 90 | 154 | [almighty-tools-gmc-cl.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-cl.xml) |
| Colombia | es | COP | 90 | 154 | [almighty-tools-gmc-co.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-co.xml) |
| Germany | en | EUR | 76 | 142 | [almighty-tools-gmc-de.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-de.xml) |
| Denmark | en | EUR | 76 | 142 | [almighty-tools-gmc-dk.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-dk.xml) |
| Spain | en | EUR | 76 | 142 | [almighty-tools-gmc-es.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-es.xml) |
| Finland | en | EUR | 76 | 142 | [almighty-tools-gmc-fi.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-fi.xml) |
| France | fr | EUR | 90 | 154 | [almighty-tools-gmc-fr.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-fr.xml) |
| United Kingdom | en | GBP | 76 | 142 | [almighty-tools-gmc-gb.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-gb.xml) |
| Greece | en | EUR | 76 | 142 | [almighty-tools-gmc-gr.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-gr.xml) |
| Ireland | en | EUR | 76 | 142 | [almighty-tools-gmc-ie.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-ie.xml) |
| Israel | en | ILS | 76 | 142 | [almighty-tools-gmc-il.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-il.xml) |
| Italy | en | EUR | 76 | 142 | [almighty-tools-gmc-it.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-it.xml) |
| Japan | en | JPY | 76 | 142 | [almighty-tools-gmc-jp.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-jp.xml) |
| Mexico | es | MXN | 90 | 154 | [almighty-tools-gmc-mx.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-mx.xml) |
| Netherlands | en | EUR | 76 | 142 | [almighty-tools-gmc-nl.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-nl.xml) |
| Norway | en | EUR | 76 | 142 | [almighty-tools-gmc-no.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-no.xml) |
| New Zealand | en | USD | 76 | 142 | [almighty-tools-gmc-nz.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-nz.xml) |
| Portugal | en | EUR | 76 | 142 | [almighty-tools-gmc-pt.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-pt.xml) |
| Sweden | en | EUR | 76 | 142 | [almighty-tools-gmc-se.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-se.xml) |
| Singapore | en | SGD | 76 | 142 | [almighty-tools-gmc-sg.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-sg.xml) |
| United States (Spanish) | es | USD | 76 | 142 | [almighty-tools-gmc-us-es.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-us-es.xml) |

English is preserved for the 14 European countries already configured with an English source in Merchant Center; France is French; Mexico, Argentina, Colombia, Chile and the additional US source are Spanish. Canada/Australia/New Zealand/Brazil/UAE use USD according to current Shopify Markets settings. Europe uses EUR even in non-EUR-native countries. Google requires matching landing/checkout currency and shipping currency when using conversion.
