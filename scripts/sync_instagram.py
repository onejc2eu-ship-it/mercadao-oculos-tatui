#!/usr/bin/env python3
"""Atualiza feed público usando Instagram Graph API. Credenciais só via secrets."""
import json,os,urllib.request,urllib.parse,datetime,pathlib,sys
TOKEN=os.environ.get('INSTAGRAM_ACCESS_TOKEN')
ACCOUNT=os.environ.get('INSTAGRAM_ACCOUNT_ID')
if not TOKEN or not ACCOUNT:
    sys.exit('Defina INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID nos Secrets do repositório.')
fields='id,caption,media_type,media_url,thumbnail_url,permalink,timestamp'
url='https://graph.facebook.com/v24.0/'+urllib.parse.quote(ACCOUNT,safe='')+'/media?'+urllib.parse.urlencode({'fields':fields,'limit':12,'access_token':TOKEN})
req=urllib.request.Request(url,headers={'User-Agent':'TatuiInstagramFeed/1.0'})
with urllib.request.urlopen(req,timeout=25) as response:
    payload=json.load(response)
posts=[]
for p in payload.get('data',[]):
    link=p.get('permalink','')
    if not link.startswith(('https://www.instagram.com/p/','https://www.instagram.com/reel/')):continue
    posts.append({k:p[k] for k in ('id','caption','media_type','media_url','thumbnail_url','permalink','timestamp') if k in p})
posts.sort(key=lambda p:p.get('timestamp',''),reverse=True)
if not posts:sys.exit('Nenhuma publicação válida retornada; arquivo existente preservado.')
path=pathlib.Path(__file__).resolve().parents[1]/'instagram-feed.json'
path.write_text(json.dumps({'updated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'posts':posts[:6]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Sincronizadas',len(posts[:6]),'publicações.')
