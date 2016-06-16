#!/usr/bin/env python3

import sys, os, json, io
import argparse
import asyncio

from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs

from aiohttp import web

import smatch_api
from rules import generate_document_rules

port = 9000
host = '0.0.0.0'

processor = smatch_api.AMRProcessor()
threadpool = ThreadPoolExecutor(2)

async def parse_test(request):

    qs = parse_qs(request.query_string)

    try: seed = int(qs.get('seed'))
    except: seed = None

    # start response right away to send keep-alive header
    headers = {}
    headers['Connection'] = 'Keep-Alive'
    headers['Keep-Alive'] = 'timeout=1500, max=100'
    content_type = 'application/json; charset=utf-8'
    headers['Content-Type'] = content_type
    response = web.StreamResponse(headers=headers)
    response.prepare(request)
    response.start(request)

    with open("sample.gold", encoding='utf8', errors='replace') as gf, open("sample.silver", encoding='utf8', errors='replace') as sf:
        document = await processor(gf, sf, False, seed=seed)
        print("ok")

    # generate_document_rules(document)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(threadpool, lambda document: generate_document_rules(document), document)

    print('Sending response...')
    # write response data
    response.write(json.dumps(document, indent=4, ensure_ascii=False).encode('utf8'))
    await response.write_eof()
    await response.drain()
    print('Response sent!')

    return response
    # return web.Response(body=json.dumps(document, indent=4, ensure_ascii=False).encode('utf8'), content_type=content_type)


async def parse_match_amr(request):

    data = json.loads((await request.read()).decode('utf8', errors='ignore'))

    qs = parse_qs(request.query_string)

    try: seed = int(qs.get('seed'))
    except: seed = None

    # start response right away to send keep-alive header
    headers = {}
    headers['Connection'] = 'Keep-Alive'
    headers['Keep-Alive'] = 'timeout=1500, max=100'
    content_type = 'application/json; charset=utf-8'
    headers['Content-Type'] = content_type
    response = web.StreamResponse(headers=headers)
    response.prepare(request)
    response.start(request)

    with io.StringIO(data['left']) as left, io.StringIO(data['right']) as right:
        document = await processor(left, right, False, seed=seed)
        print("ok")

    # generate_document_rules(document)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(threadpool, lambda document: generate_document_rules(document), document)

    print('Sending response...')
    # write response data
    response.write(json.dumps(document, indent=4, ensure_ascii=False).encode('utf8'))
    await response.write_eof()
    await response.drain()
    print('Response sent!')

    return response
    # return web.Response(body=json.dumps(document, indent=4, ensure_ascii=False).encode('utf8'), content_type=content_type)


async def static_file(request):
    try:
        path = request.match_info.get('path') or 'index.html'
        root = 'static/app'
        with open(os.path.join(root, path), 'rb') as f:
            content_type = 'text/plain'
            ext = os.path.splitext(path)[1].lower()
            # https://www.sitepoint.com/web-foundations/mime-types-complete-list/
            if ext in ('.html', '.htm'):
                content_type = 'text/html'
            elif ext in ('.css'):
                content_type = 'text/css'
            elif ext in ('.js'):
                content_type = 'application/javascript' # or application/x-javascript ; text/javascript ; application/ecmascript
            elif ext in ('.json'):
                content_type = 'application/'
            elif ext in ('.jpg', '.jpeg'):
                content_type = 'application/jpeg'
            elif ext in ('.png', '.png'):
                content_type = 'application/png'

            return web.Response(body=f.read(), content_type=content_type)
    except FileNotFoundError:
        raise web.HTTPNotFound

def init():
    app = web.Application()
    app.get = lambda path: (lambda fn: app.router.add_route('GET', path, fn))

    app.router.add_resource(r'/api/parse_match_amr').add_route('POST', parse_match_amr)
    app.router.add_resource(r'/api/test_data').add_route('GET', parse_test)
    app.router.add_resource(r'/{path:.*}').add_route('GET', static_file)
    web.run_app(app, host=args.host, port=args.port)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='VisualSMATCH server', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--host', type=str, default=host, help='listen host ip, 0.0.0.0 for all interfaces')
    parser.add_argument('--port', type=int, default=port, help='listen port number')

    args = parser.parse_args()

    init()
