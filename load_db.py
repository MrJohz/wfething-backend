import os
import sys
import gzip
import sqlite3
import pathlib

import arrow
from lxml import etree
import requests
import kaptan

from wfeconfig import WFEConfig

NATIONSTATES_URL = "http://www.nationstates.net/pages/regions.xml.gz"
AFFORESS_URL_ONE = "http://dailydumps.s3-us-west-2.amazonaws.com/regions/{date_str}-regions.xml.gz"
AFFORESS_URL_TWO = "http://dailydumps.s3-us-west-2.amazonaws.com/regions/{year}/{date_str}-regions.xml.gz"

SQL_PHRASE_CREATE_TABLE = "CREATE TABLE IF NOT EXISTS regions (lcname TEXT, name TEXT, wfe TEXT, date INT)"
SQL_PHRASE_SELECT = "SELECT wfe FROM regions WHERE lcname = ? AND date < ? AND wfe NOT NULL ORDER BY date DESC LIMIT 1"
SQL_PHRASE_INSERT_EMPTY = "INSERT INTO regions (lcname,name,wfe,date) VALUES (?, ?, NULL, ?)"
SQL_PHRASE_INSERT_FULL = "INSERT INTO regions (lcname,name,wfe,date) VALUES (?, ?, ?, ?)"
SQL_PHRASE_GET_INDEX = "SELECT * FROM sqlite_master WHERE type='index' AND tbl_name='regions'"
SQL_PHRASE_ADD_INDEX = "CREATE INDEX idx1 ON regions(lcname,date)"
SQL_PHRASE_ANALYSE = "ANALYZE regions"


def simple(name):
    return name.replace(' ', '_').lower()


def elements(filename, tag=None):
    gzfile = gzip.open(filename, 'rb')
    for event, element in etree.iterparse(gzfile, tag=tag):
        yield element
        element.clear()


def regions(filename, mktime):
    """A generator function that iterates through all 'REGION'
    elements in the dump, and yields on each call a dictionary
    containing the region's name, wfe, embassies, and the date
    that this dump was created (supplied as an arrow object via
    `mktime`.)"""
    for region in elements(str(filename), tag="REGION"):
        name = region.find('NAME').text
        date = mktime.format('YYYY-MM-DD')
        wfe = region.find('FACTBOOK').text
        #embs = defaultdict(list)
        #for e in region.find('EMBASSIES'):
        #    for tpe in EMBTYPES:
        #        if e.attrib.get('type') is not None:
        #            embs[tpe].append(e.text)
        #            break
        #    else:
        #        embs['normal'].append(e.text)
        yield {'lcname': simple(name), 'name': name, 'wfe': wfe, 'date': date}


def download_file(req, url, filepath):
    r = req.get(url, stream=True)
    with filepath.open(mode='wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()

    return filepath


def download(useragent, tmp_dir, date=None):
    requester = requests.Session()
    requester.headers.update({'user-agent': useragent})

    filepath = tmp_dir / 'rdump.xml.gz'

    if date is None:
        fp = download_file(requester, NATIONSTATES_URL, filepath)
    else:
        datestr = date.format('YYYY-MM-DD')
        if date.year in [2011, 2012, 2013]:
            url = AFFORESS_URL_TWO.format(year=date.year, date_str=datestr)
        else:
            url = AFFORESS_URL_ONE.format(date_str=datestr)
        fp = download_file(requester, url, filepath)

    return fp


def save_to_database(db, rdict, date):
    for row in db.execute(SQL_PHRASE_SELECT, (rdict['lcname'], date.timestamp)):
        if row['wfe'] == rdict['wfe']:
            db.execute(SQL_PHRASE_INSERT_EMPTY, (rdict['lcname'], rdict['name'], date.timestamp))
            break
        else:
            db.execute(SQL_PHRASE_INSERT_FULL, (rdict['lcname'], rdict['name'], rdict['wfe'], date.timestamp))
            break
    else: # no results found for region, or all results had null wfe
        db.execute(SQL_PHRASE_INSERT_FULL, (rdict['lcname'], rdict['name'], rdict['wfe'], date.timestamp))


def parse_args(args):
    config = "config.ini"
    date = None
    verbose = False

    for arg in args:
        if arg.startswith('--config='):
            config = arg[9:]
        elif arg.startswith('--date='):
            date = arg[7:]
            date = arrow.get(date, 'YYYY-MM-DD')
        elif arg == "--verbose":
            verbose = True

    config_format = kaptan.HANDLER_EXT.get(os.path.splitext(config)[1][1:], None)

    config = WFEConfig(config, format=config_format)
    return {"date": date, "config": config, "verbose": verbose}


def main(config, date=None, verbose=False):

    if verbose:
        print("Downloading file")
    fp = download(config['load_db.useragent'], pathlib.Path(config['load_db.tmp_dir']), date)
    if verbose:
        print("File Downloaded")
    #fp = pathlib.Path(config['load_db.tmp_dir']) / 'rdump.xml.gz'

    if date is None:
        date = arrow.utcnow()

    conn = sqlite3.connect(config['general.db_file'])
    conn.row_factory = sqlite3.Row
    if verbose:
        print("SQL Connection initiated")

    db = conn.cursor()

    db.execute(SQL_PHRASE_GET_INDEX)
    if db.fetchone() is not None:
        if verbose:
            print("Adding indexes to db")
        db.execute(SQL_PHRASE_ADD_INDEX)
        db.execute(SQL_PHRASE_ANALYSE)

    db.execute(SQL_PHRASE_CREATE_TABLE)

    if verbose:
        print("Obtaining regions")
    for region in regions(fp, date):
        save_to_database(db, region, date)

    conn.commit()
    conn.close()

    if verbose:
        print("All done")

if __name__ == "__main__":
    main(**parse_args(sys.argv))
