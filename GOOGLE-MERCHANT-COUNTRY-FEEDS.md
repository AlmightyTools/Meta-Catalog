# Almighty Tools Google Merchant country feeds

Updated: 2026-10-09 UTC.

29 country files, all in English. France and Latin America will receive separate localized feeds after complete frontend translations. Meta feed files remain independent.

## Generation and landing pages

- US workflow: [Google Merchant US owned feed](https://api.romanov.kim/workflow/YpAkJgKt9UmShjiL), daily 05:10 UTC.
- Other countries: [Google Merchant owned country feeds](https://api.romanov.kim/workflow/y4JecM16QSlVln38), daily 05:25 UTC.
- Shopify active and country-published products only. Service add-ons, screws, priority processing, shipping insurance and mystery gifts excluded. Regional French/Spanish duplicate cards excluded from English feeds.
- Prices, sale prices, currencies and availability use Shopify. Australia, Canada, New Zealand, Brazil and UAE currently sell in USD; non-EUR European countries currently use EUR, per Shopify Markets.
- Links go to `https://almighty.tools/products/...` with an explicit variant and country (and currency for international files). The country remains stable even with a stored preference or different IP. Initial HTML and structured data show the selected offer. UTM parameters are preserved when changing country; existing consent/privacy processing remains applicable.
- Genuine, approved original photos are reused; no generated product art. Google product category, actual variant details and country/product-type labels are included directly in each primary XML.
- `almighty-tools-gmc-us-es.xml` is a legacy candidate, no longer updated or intended for new registration.
- The live site implementation is [storefront PR 168](https://github.com/AlmightyTools/almighty-tools-store/pull/168).

## Merchant Center cutover

Files and successful generation do not prove Google approval. New primary sources use country-specific `CC_OWNED_TEST` feed labels and Free listings only until price/image/shipping diagnostics are verified. Existing Shopify/agency sources and Shopping Ads campaigns remain active pending a controlled cutover. Google Ads consumes the linked Merchant account; do not upload these XML files separately into Ads.

No Local Inventory file is generated: no physical store was linked. Attributes already present in these primary files do not need a duplicate supplemental source. Existing supplemental technical claims should be reviewed, not blindly copied.

24 countries have 76 products / 142 offers; Argentina, Chile, Colombia, France and Mexico have 70 / 120 because Shopify does not publish Quad Socket Pro Bundle, Backpack, Blaster and three Ruler alias cards there. Count reflects current market publication, not a file-size cap.

## Raw feed URLs

| Country | Language | Currency | Products | Offers | Feed |
|---|---|---|---:|---:|---|
| United Arab Emirates (AE) | en | USD | 76 | 142 | [almighty-tools-gmc-ae.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-ae.xml) |
| Argentina (AR) | en | ARS | 70 | 120 | [almighty-tools-gmc-ar.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-ar.xml) |
| Austria (AT) | en | EUR | 76 | 142 | [almighty-tools-gmc-at.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-at.xml) |
| Australia (AU) | en | USD | 76 | 142 | [almighty-tools-gmc-au.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-au.xml) |
| Belgium (BE) | en | EUR | 76 | 142 | [almighty-tools-gmc-be.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-be.xml) |
| Brazil (BR) | en | USD | 76 | 142 | [almighty-tools-gmc-br.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-br.xml) |
| Canada (CA) | en | USD | 76 | 142 | [almighty-tools-gmc-ca.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-ca.xml) |
| Switzerland (CH) | en | EUR | 76 | 142 | [almighty-tools-gmc-ch.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-ch.xml) |
| Chile (CL) | en | CLP | 70 | 120 | [almighty-tools-gmc-cl.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-cl.xml) |
| Colombia (CO) | en | COP | 70 | 120 | [almighty-tools-gmc-co.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-co.xml) |
| Germany (DE) | en | EUR | 76 | 142 | [almighty-tools-gmc-de.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-de.xml) |
| Denmark (DK) | en | EUR | 76 | 142 | [almighty-tools-gmc-dk.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-dk.xml) |
| Spain (ES) | en | EUR | 76 | 142 | [almighty-tools-gmc-es.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-es.xml) |
| Finland (FI) | en | EUR | 76 | 142 | [almighty-tools-gmc-fi.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-fi.xml) |
| France (FR) | en | EUR | 70 | 120 | [almighty-tools-gmc-fr.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-fr.xml) |
| United Kingdom (GB) | en | GBP | 76 | 142 | [almighty-tools-gmc-gb.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-gb.xml) |
| Greece (GR) | en | EUR | 76 | 142 | [almighty-tools-gmc-gr.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-gr.xml) |
| Ireland (IE) | en | EUR | 76 | 142 | [almighty-tools-gmc-ie.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-ie.xml) |
| Israel (IL) | en | ILS | 76 | 142 | [almighty-tools-gmc-il.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-il.xml) |
| Italy (IT) | en | EUR | 76 | 142 | [almighty-tools-gmc-it.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-it.xml) |
| Japan (JP) | en | JPY | 76 | 142 | [almighty-tools-gmc-jp.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-jp.xml) |
| Mexico (MX) | en | MXN | 70 | 120 | [almighty-tools-gmc-mx.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-mx.xml) |
| Netherlands (NL) | en | EUR | 76 | 142 | [almighty-tools-gmc-nl.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-nl.xml) |
| Norway (NO) | en | EUR | 76 | 142 | [almighty-tools-gmc-no.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-no.xml) |
| New Zealand (NZ) | en | USD | 76 | 142 | [almighty-tools-gmc-nz.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-nz.xml) |
| Portugal (PT) | en | EUR | 76 | 142 | [almighty-tools-gmc-pt.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-pt.xml) |
| Sweden (SE) | en | EUR | 76 | 142 | [almighty-tools-gmc-se.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-se.xml) |
| Singapore (SG) | en | SGD | 76 | 142 | [almighty-tools-gmc-sg.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-sg.xml) |
| United States (US) | en | USD | 76 | 142 | [almighty-tools-gmc-us.xml](https://raw.githubusercontent.com/AlmightyTools/Meta-Catalog/main/almighty-tools-gmc-us.xml) |
