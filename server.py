#!/usr/bin/env python3

import sys, os, json, io
import asyncio
import argparse

from bottle import Bottle, abort, static_file, run, auth_basic, hook

import smatch_api
from rules import generate_document_rules

try:
    asyncio.tasks.CoroWrapper = asyncio.tasks.coroutines.CoroWrapper # quickfix for bottle
except:
    pass

port = 9000
host = '0.0.0.0'

parser = argparse.ArgumentParser(description='VisualSMATCH server', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--host', type=str, default=host, help='listen host ip, 0.0.0.0 for all interfaces')
parser.add_argument('--port', type=int, default=port, help='listen port number')

args = parser.parse_args()


app = Bottle()


# https://gist.github.com/richard-flosi/3789163
# @app.hook('after_request')
@app.hook('before_request')
def keep_alive(request, response):
    response.headers['Connection'] = 'Keep-Alive'
    response.headers['Keep-Alive'] = 'timeout=1500, max=100'
    # print(response.headers)
    # for k,v in response.headers.items():
    #     print(k, ':', v)

@app.get('/api/test_data')
def test_amr(request, response):
    # sample data from: http://amr.isi.edu/download/amr-bank-struct-v1.5.txt
    with open("sample.gold", encoding='utf8', errors='replace') as gf, open("sample.silver", encoding='utf8', errors='replace') as sf:
        seed = request.query.get('seed')
        if not seed:
            seed = None
        else:
            try:
                seed = int(seed)
            except:
                seed = None
        smatch_api.smatch.seed = seed
        document = smatch_api.make_matched_document(gf, sf, False)
        print("ok")
    generate_document_rules(document)
    response.status = '200 OK'
    response.content_type = 'application/json; charset=utf-8'
    data = json.dumps(document, indent=4)
    print('Sending data...')
    return data

@app.get('/api/parse_match_amr')
@app.post('/api/parse_match_amr')
def parse_match_amr(request, response):
    data = json.loads(request.body.read().decode('utf8', errors='ignore'))
    with io.StringIO(data['left']) as left, io.StringIO(data['right']) as right:
        smatch_api.smatch.seed = data.get('seed', None)
        document = smatch_api.make_matched_document(left, right, False)
        print("ok")
    generate_document_rules(document)
    response.status = '200 OK'
    response.content_type = 'application/json; charset=utf-8'
    data = json.dumps(document, indent=4)
    print('Sending data...')
    return data

# @app.get('/api/parse_amr')
# @app.post('/api/parse_amr')
# def parse_amr(request, response):
#     body = request.body.read().decode('utf8', errors='ignore')
#     lines = body.split('\n')
#     data = amr_reader.extract_triples(amr_reader.parse_amr_lines(lines))
#     response.status = '200 OK'
#     response.content_type = 'application/json; charset=utf-8'
#     return json.dumps(data, indent=4)

# static content (webpage files: *.html, *.js, *.css etc.)
@app.route('/')
@app.route('/<path:path>')
def static(request, response, path='index.html'):
    return static_file(request, path, root=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static/app'))
    # return static_file(path, root=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dest'))


# run(app, host='0.0.0.0', port=port, debug=False, reloader=False)
run(app, host=args.host, port=args.port, debug=False, reloader=False)
