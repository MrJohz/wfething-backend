import os
import json
import html

from bottle import Bottle, run, request, response
from bottle_sqlite import SQLitePlugin
import kaptan

from wfeconfig import WFEConfig

config_format = kaptan.HANDLER_EXT.get(os.path.splitext('config.ini')[1][1:], None)
config = WFEConfig('config.ini', format=config_format)

def simple(name):
    return name.replace(' ', '_').lower()

def decode(wfe):
    wfe = wfe.replace('&amp;', '&')
    return html.unescape(wfe)

app = Bottle()
app.install(SQLitePlugin(dbfile=config['general.db_file']))

@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'

@app.route('/')
def list_all(db):
    response.content_type = 'application/json'

    jsn = {'names': [row['name'] for row in db.execute("SELECT DISTINCT name FROM regions")]}

    if request.params.get('pretty') is not None:
        return json.dumps(jsn, indent=4)

    return json.dumps(jsn, separators=(',',':'))

@app.route('/<name>')
def get_region(db, name):
    jsn = {'data': []}

    response.content_type = 'application/json'

    name = simple(name)
    fullname = None

    last_wfe = ''
    for row in db.execute("SELECT * FROM regions WHERE lcname=? ORDER BY date", (name,)):
        entry = dict(row)
        if entry['wfe'] is not None:
            entry['wfe'] = decode(entry['wfe'])
            last_wfe = entry['wfe']
        else:
            entry['wfe'] = last_wfe

        fullname = entry.pop('name')
        del entry['lcname']
        jsn['data'].insert(0, entry)

    jsn['name'] = fullname

    if request.params.get('pretty') is not None:
        return json.dumps(jsn, indent=4)
    return json.dumps(jsn, separators=(',', ':'))

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        print("Running debug server")
        run(app, host='localhost', port=config['server.port'], debug=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "cherry":
        print("Running debug cherrypy server")
        run(app, host='localhost', server='cherrypy', port=config['server.port'], debug=True)
    else:
        print("Running production cherrypy server")
        run(app, host='localhost', server='cherrypy', port=config['server.port'])
