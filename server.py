#!/usr/bin/python
import sys,os
import re
import pprint
import time

sys.path.append('lib')
import simplejson
import jsonpickle
import transcript
import joiner
import pagearizer

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from contextlib import closing


#configuration
DEBUG      = True
PER_PAGE   = 20
SECRET_KEY = 'development key'
DATABASE   = 'db.json'


#application code
db         = None
headers    = None
queries    = {}

MAX_QUERY_BUFFER = 100

#class MyFlask(Flask):
#    def get_send_file_max_age(self, name):
#        if name.lower().endswith('.js'):
#            return 604800
#        if name.lower().endswith('.css'):
#            return 604800
#        #if name.lower().endswith('.png'):
#        #    return 604800
#        return super(Flask).get_send_file_max_age(self, name)
#
#app = MyFlask(__name__)


app        = Flask(__name__)
app.config.from_object(__name__)
app.jinja_env.globals['url_for_other_page'] = pagearizer.url_for_other_page

#APPLICATION CODE :: SETUP
@app.before_request
def before_request():
    g.db, g.headers, g.queries = getDb()
    h = g.headers.keys()
    h.sort()
    h.reverse()
    i = {}
    for k in h:
        i[k] = g.headers[k].keys()
        i[k].sort()
    g.headersNames = h
    g.colsNames    = i


@app.after_request
def after_request(response):
    #g.db.close()
    return response


@app.teardown_request
def teardown_request(exception):
    #g.db.close()
    pass


#APPLICATION CODE :: ROUTE
@app.route('/query/<int:page>', methods=['POST'])
def query(page):
    sessionId = time.time()
    if session.get('id'):
        sessionId     = session['id']
        print "getting stored ID %s" % (sessionId)
    else:
        session['id'] = sessionId
        print "storing new ID %s" % (sessionId)


    qry = {}
    if request.method == 'POST':
        print "POST method %s" % (request.form)
        for field, value in request.form.items():
            val = request.form[field]
            qry[field] = val
            print "field %s value %s" % (field, val)

        #flash('new entry was successfully posted')

    res = queryBuffer(sessionId, qry)

    count    = len(res)
    if count > 0:
        maxPage  = count/PER_PAGE

        if float(count)/PER_PAGE > maxPage:
            maxPage += 1

        if page > maxPage:
            page = maxPage


        perc     = int((float(page) / maxPage) * 100)
        beginPos = (page  - 1) * PER_PAGE

        print "  count %d page %d max page %d perc %d%% begin pos %d" % (count, page, maxPage, perc, beginPos)

        resPage  = getResultForPage(res, page, PER_PAGE, count)
        resKeys  = resPage.keys()
        resKeys.sort(key=transcript.sortNode)

        resTemp = render_template('response.html', page=page, count=count, maxPage=maxPage, perc=perc, beginPos=beginPos, resPage=resPage, resKeys=resKeys);
        return resTemp
    else:
        resTemp = render_template('response.html', page=0,    count=count)
        return resTemp


@app.route('/', methods=['GET'])
def initial():
    sessionId = time.time()
    if session.get('id'):
        sessionId     = session['id']
        print "getting stored ID %s" % (sessionId)
    else:
        session['id'] = sessionId
        print "storing new ID %s" % (sessionId)

    resTemp = render_template('index.html')
    return resTemp


#APPLICATION CODE :: ACESSORY FUNCTIONS
def queryBuffer(sessionId, qry):
    if sessionId not in g.queries:
        print g.queries.keys()
        g.queries[sessionId] = []

    res = None
    if len(g.queries[sessionId]) == 0:
        res = None
        print "no queries to session %s" % (str(sessionId))

    else:
        if qry in [x[0] for x in g.queries[sessionId]]:
            print "session %s has qry in store (%d)" % (str(sessionId), len(g.queries[sessionId]))

            for i in range(len(g.queries[sessionId])):
                lqry, lres = g.queries[sessionId][i]
                print "%d: %s vs %s" % (i, lqry, qry)
                if lqry == qry:
                    res = lres
                    g.queries[sessionId].pop(i)
                    g.queries[sessionId].append([lqry, lres])
                    print "  session %s has qry at position %d" % (str(sessionId), i)
                    break

        else:
            print "session %s does not have qry in store" % (str(sessionId))
            res = None

    if res is None:
        print "querying"
        res = getResult(g.db, qry)
        g.queries[sessionId].append([qry, res])
        if len(g.queries[sessionId]) > MAX_QUERY_BUFFER:
            g.queries.pop(0)

    return res


def getResult(db, qry):
    dbN = {}

    

    return dbN


def getResultForPage(res, page, num_per_page, count):
    resKeys = res.keys()
    resKeys.sort(key=transcript.sortNode)
    print "        getting page %d" % page
    begin  = (page - 1) * num_per_page
    end    = (page      * num_per_page)
    lenRes = len(res)

    if end > lenRes:
        end = lenRes

    if begin > end:
        begin = end - num_per_page

    print "          len %d begin %d end %d" % (lenRes, begin, end)

    resp    = resKeys[begin: end]
    outvals = {}
    for k in resp:
        outvals[k] = res[k]

    return outvals



#db
def init_db(dbfile):
    with app.app_context():
        print "initializing db"
        if not os.path.exists(dbfile):
            print "NO DATABASE FILE %s" % dbfile
            sys.exit(1)

        global db
        global headers
        global queries

        jsonpickle.set_preferred_backend('simplejson')
        jsonpickle.set_encoder_options('simplejson', sort_keys=True, indent=1)
        data = open(dbfile, 'r').read()

        db, tranlatedHeaders, lHeaders, lHeadersPos, lKeys = jsonpickle.decode(data)
        transcript.transcriptdata.headers, transcript.transcriptdata.headersPos, transcript.transcriptdata.keys = lHeaders, lHeadersPos, lKeys

        headers = tranlatedHeaders

        #pprint.pprint(db)
        #sys.exit(0)
        if db is None:
            print "no data in database"
            sys.exit(1)

        if len(db) == 0:
            print "database is empty"
            sys.exit(1)

        print "db loaded. %d entries" % len(db)


def getDb():
    if db is None:
        init_db(DATABASE)
    return [db, headers, queries]

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        joiner.main()
    app.run()




#@app.route('/add', methods=['POST'])
#def add_entry():
#    if not session.get('logged_in'):
#        abort(401)
#    g.db.execute('insert into entries (title, text) values(?,?)', \
#                 [request.form['title'], request.form['text']])
#    g.db.commit()
#    flash('new entry was successfully posted')
#    return redirect(url_for('show_entries'))
#
#@app.route('/login', methods=['GET', 'POST'])
#def login():
#    error = None
#    if request.method == 'POST':
#        if   request.form['username'] != app.config['USERNAME']:
#            error = "Invalid username"
#        elif request.form['password'] != app.config['PASSWORD']:
#            error = "Invalid password"
#        else:
#            session['logged_in'] = True
#            flash('you were logged in')
#            return redirect(url_for('show_entries'))
#    return render_template('login.html', error=error)
#
#@app.route('/logout')
#def logout():
#    session.pop('logged_in', None)
#    flash('you were logged out')
#    return redirect(url_for('show_entries'))
