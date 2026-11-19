#!/usr/bin/env python3
"""Atualiza o feed público (instagram-feed.json) usando a Instagram Graph API.

Credenciais: somente por variáveis de ambiente (Secrets do GitHub), nunca no código.
Se a API falhar ou não devolver publicações válidas, o arquivo anterior é preservado.
"""
import datetime
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

API_VERSION = os.environ.get('GRAPH_API_VERSION', 'v24.0')
TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN')
ACCOUNT = os.environ.get('INSTAGRAM_ACCOUNT_ID')
FIELDS = 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp'
MAX_POSTS = 6
VALID_PREFIXES = ('https://www.instagram.com/p/', 'https://www.instagram.com/reel/')
OUT_PATH = pathlib.Path(__file__).resolve().parents[1] / 'instagram-feed.json'


def fetch_media():
    query = urllib.parse.urlencode({'fields': FIELDS, 'limit': 12, 'access_token': TOKEN})
    url = f'https://graph.facebook.com/{API_VERSION}/{urllib.parse.quote(ACCOUNT, safe="")}/media?{query}'
    req = urllib.request.Request(url, headers={'User-Agent': 'TatuiInstagramFeed/1.1'})
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = ''
        try:
            err = json.load(exc).get('error', {})
            detail = f" tipo={err.get('type')} código={err.get('code')} mensagem={err.get('message')}"
        except Exception:
            pass
        sys.exit(f'Erro HTTP {exc.code} da Graph API.{detail} (arquivo existente preservado; '
                 'se for token expirado ou revogado, gere um novo e atualize o Secret).')
    except (urllib.error.URLError, TimeoutError) as exc:
        sys.exit(f'Falha de rede ao consultar a Graph API: {exc} (arquivo existente preservado).')


def normalize_timestamp(value):
    """A API devolve 2026-11-18T17:27:34+0000; converte para +00:00 (aceito por todos os navegadores)."""
    try:
        return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z').isoformat()
    except (TypeError, ValueError):
        return value


def build_posts(payload):
    posts = []
    for p in payload.get('data', []):
        if not p.get('permalink', '').startswith(VALID_PREFIXES):
            continue
        item = {k: p[k] for k in ('id', 'caption', 'media_type', 'permalink') if k in p}
        # Vídeo: o site usa só a miniatura; não guarda o endereço (longo e temporário) do arquivo de vídeo.
        if p.get('media_type') != 'VIDEO' and p.get('media_url'):
            item['media_url'] = p['media_url']
        if p.get('thumbnail_url'):
            item['thumbnail_url'] = p['thumbnail_url']
        if p.get('timestamp'):
            item['timestamp'] = normalize_timestamp(p['timestamp'])
        posts.append(item)
    posts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return posts[:MAX_POSTS]


def main():
    if not TOKEN or not ACCOUNT:
        sys.exit('Defina INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID nos Secrets do repositório.')
    posts = build_posts(fetch_media())
    if not posts:
        sys.exit('Nenhuma publicação válida retornada; arquivo existente preservado.')
    data = {
        'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'posts': posts,
    }
    tmp = OUT_PATH.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, OUT_PATH)
    print('Sincronizadas', len(posts), 'publicações.')


if __name__ == '__main__':
    main()
