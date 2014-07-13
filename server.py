import os

from bottle import Bottle, run, request
from bottle_sqlite import SQLitePlugin
import kaptan

from wfeconfig import WFEConfig

config_format = kaptan.HANDLER_EXT.get(os.path.splitext('config.ini')[1][1:], None)
config = WFEConfig('config.ini', format=config_format)

app = Bottle()
app.install(SQLitePlugin(dbfile=config['general.db_file']))

@app.route('/')
def list_all(db):
    return {'names': [dict(row) for row in db.execute("SELECT DISTINCT name, lcname FROM regions")]}

@app.route('/<name>')
def get_region(db, name):
    jsn = {'data': []}

    last_wfe = ''
    for row in db.execute("SELECT * FROM regions WHERE lcname=? ORDER BY date", (name,)):
        entry = dict(row)
        if entry['wfe'] is not None:
            last_wfe = entry['wfe']
        else:
            entry['wfe'] = last_wfe
        jsn['data'].insert(0, entry)

    return jsn

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "debug":
    run(app, host='localhost', port=8080, debug=True)

application = app
