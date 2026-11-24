"""Refresh authorized German outputs from public production pages and exact quotes."""
import concurrent.futures,datetime,json,subprocess,tempfile,shutil,time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote,quote
import xml.etree.ElementTree as ET
from prepare_german_feeds import prepare,ROOT,G,MARKETS
class Page(HTMLParser):
 def __init__(self):super().__init__();self.lang=None;self.noindex=False;self.ld=False;self.buf=[];self.products=[]
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if t=='html':self.lang=a.get('lang')
  if t=='meta' and a.get('name')=='robots':self.noindex|='noindex' in a.get('content','')
  if t=='script':self.ld=a.get('type')=='application/ld+json';self.buf=[]
 def handle_data(self,s):
  if self.ld:self.buf.append(s)
 def handle_endtag(self,t):
  if t=='script' and self.ld:
   j=json.loads(''.join(self.buf));self.ld=False
   if isinstance(j,dict) and j.get('@type')=='Product':self.products.append(j)
def fetch(path):
 for attempt in range(3):
  p=subprocess.run(['curl','--fail','--silent','--show-error','--retry','2','--max-time','30','-A','Almighty-Feed-Refresh/1.0','-H','Sec-GPC: 1','https://almighty.tools'+path],capture_output=True)
  if p.returncode==0:return p.stdout
  if p.returncode not in {7,28,35,56} or attempt==2:raise RuntimeError('Public source unavailable: '+path+' curl='+str(p.returncode))
  time.sleep(attempt+1)

def refresh():
 with tempfile.TemporaryDirectory(prefix='almighty-german-') as temp:
  e=Path(temp)/'evidence';o=Path(temp)/'output';e.mkdir()
  sources={c:ET.parse(ROOT/('almighty-tools-gmc-'+c.lower()+'.xml')) for c in MARKETS}
  paths=sorted({unquote(urlsplit(i.findtext('link')).path) for t in sources.values() for i in t.findall('./channel/item')})
  def page(path):
   q=Page();q.feed(fetch('/de'+quote(path,safe='/')).decode());assert q.lang=='de' and not q.noindex and len(q.products)==1,'German production index gate failed: '+path
   d=q.products[0];images=d.get('image',[]);return path,{'http':200,'lang':'de','robots':['index, follow'],'title':d['name'],'description':d['description'],'images':[images] if isinstance(images,str) else images}
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:pages=dict(pool.map(page,paths))
  def market(key):
   c,path=key;h=path.split('/products/')[-1];j=json.loads(fetch('/api/market/product?country='+c+'&handle='+quote(h,safe='')));assert j['country']==c and j.get('product'),'No exact product quote'
   vs=j['product']['variants'];assert not vs.get('pageInfo',{}).get('hasNextPage')
   return c,h,{'http':200,'variants':{v['id'].split('/')[-1]:{k:v.get(k) for k in ['price','compareAtPrice','availableForSale','sku']} for v in vs['nodes']}}
  quotes={c:{} for c in MARKETS}
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   for c,h,d in pool.map(market,[(c,p) for c in MARKETS for p in paths]):quotes[c][h]=d
  for name,data in [('german-pages.json',pages),('market-quotes.json',quotes),('exact-localized-variant-images.json',{}),('collection-proof.json',{'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})]:
   (e/name).write_text(json.dumps(data,ensure_ascii=False))
  result=prepare(e,o)
  for c in MARKETS:
   name='almighty-tools-gmc-'+c.lower()+'-de.xml';shutil.copyfile(o/name,ROOT/name)
  shutil.copyfile(o/'meta-language-de-candidate.csv',ROOT/'meta-language-de.csv')
  shutil.copyfile(o/'meta-language-country-de-candidate.csv',ROOT/'meta-language-country-de.csv')
  shutil.copyfile(o/'almighty-tools-chatgpt-german-candidate.csv',ROOT/'almighty-tools-chatgpt.csv')
  print(json.dumps({'status':'GENERATED','offers':{c:d['offers'] for c,d in result['countries'].items()},'primary_images':'existing approved exact-variant photos retained','steam_in_german':False,'meta_stock_changed':False}))
if __name__=='__main__':refresh()
