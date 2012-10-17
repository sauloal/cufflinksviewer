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

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response
from contextlib import closing



if not os.path.exists(joiner.setupfile):
    print "count not find setup file %s" % joiner.setupfile
    sys.exit(1)

for k,v in jsonpickle.decode(open(joiner.setupfile, 'r').read())['server'].items():
    globals()[k] = v

#CONSTANTS
#DEBUG            = True
#PER_PAGE         = 20
#MAX_QUERY_BUFFER = 100
SECRET_KEY = 'development key'


#VARIABLES
db         = None
headers    = None
queries    = {}


app        = Flask(__name__)
app.config.from_object(__name__)
app.jinja_env.globals['trim_blocks'       ] = True

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
    return response


@app.teardown_request
def teardown_request(exception):
    pass


#APPLICATION CODE :: ROUTE
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
        qrystr = request.form.keys()[0]
        print "query string %s" % qrystr
        qry = jsonpickle.decode(qrystr)
        print "qry structure", qry

    res = queryBuffer(sessionId, qry)

    count = len(res)

    flash(formatQuery(qry))

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
        resTemp = make_response("No match for query")
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
        res = getResult(g.db, g.headers, qry)
        g.queries[sessionId].append([qry, res])
        if len(g.queries[sessionId]) > MAX_QUERY_BUFFER:
            g.queries.pop(0)

    return res


def getResult(db, headers, qry):
    print "length qry %d" % len(qry)
    if len(qry) > 0:
        print "filtering"
        dbN = {}

        lists = []
        for filetype in qry:
            print '  analyzing filetype %s' % filetype
            for fieldname in qry[filetype]:
                print '    analyzing field %s' % fieldname
                if ((filetype in headers) and (fieldname in headers[filetype])):
                    valN, qryType, index    = headers[filetype][fieldname]
                    indexRes = index.res
                    qryValue = qry[filetype][fieldname]

                    if   qryType == 'selectmultiple':
                        #TODO: check if variables are from the correct type
                        #      and if the keys exists
                        lLists = []
                        for qrySelected in qryValue:
                            for i in range(len(indexRes)):
                                indexKey = indexRes[i][0]
                                indexVal = indexRes[i][1]
                                if indexKey == qrySelected:
                                    qryRes = indexVal
                                    lLists.append([filetype, fieldname, qrySelected, set(qryRes)])
                                    break
                        lists.extend(lLists)

                    elif qryType == 'rangeminmax' or qryType == 'rangeminmaxlog':
                        minVal, maxVal = qryValue.split(" - ")
                        minVal = int(minVal)
                        maxVal = int(maxVal)
                        lLists = []
                        for i in range(len(indexRes)):
                            indexKey = indexRes[i][0]
                            indexVal = indexRes[i][1]
                            if indexKey >= minVal:
                                if indexKey <= maxVal:
                                    qryRes = indexVal
                                    lLists.extend(qryRes)
                                else:
                                    break
                        lists.append([filetype, fieldname, qryValue, set(lLists)])

                    elif qryType == 'rangemin' or qryType == 'rangeminlog':
                        minVal = qryValue
                        minVal = int(minVal)
                        lLists = []
                        for i in range(len(indexRes)):
                            indexKey = indexRes[i][0]
                            indexVal = indexRes[i][1]
                            if indexKey >= minVal:
                                qryRes = indexVal
                                lLists.extend(qryRes)
                        lists.append([filetype, fieldname, qryValue, set(lLists)])

                    elif qryType == 'input':
                        lLists = []
                        for i in range(len(indexRes)):
                            indexKey = indexRes[i][0]
                            indexVal = indexRes[i][1]
                            if indexKey.contains(qryValue):
                                qryRes = indexVal
                                lLists.extend(qryRes)
                        lists.append([filetype, fieldname, qryValue, set(lLists)])

                    else:
                        print "    !! no such qry field type: %s !!" % qryType
                else:
                    print "    !! no such field %s !!" % fieldname
                    print headers[filetype].keys()

        resIds = None

        llist  = [x[3] for x in lists]
        resIds = set.intersection(*llist)

        #for llist in lists:
        #    lFileType  = llist[0]
        #    lFieldName = llist[1]
        #    lQryValue  = llist[2]
        #    lResIds    = llist[3]
        #
        #    if len(lResIds) == 0:
        #        print "    file type %s field %s qry %s yield no result" % (lFileType, lFieldName, lQryValue)
        #        resIds = set()
        #        break
        #
        #    if resIds is None:
        #        print "    file type %s field %s qry %s len %d is first result" % (lFileType, lFieldName, lQryValue, len(lResIds))
        #        resIds = set(lResIds)
        #    else:
        #        print "    file type %s field %s qry %s len %d . intersecting (%d)" % (lFileType, lFieldName, lQryValue, len(lResIds), len(resIds))
        #        resIds = set(resIds).intersection(set(lResIds))
        #        print "    file type %s field %s qry %s len %d . intersected  (%d)" % (lFileType, lFieldName, lQryValue, len(lResIds), len(resIds))
        #
        #    if len(resIds) == 0:
        #        print "    colapsed to length 0"
        #        break

        print "    final list has %d entries" % (len(resIds))

        for resId in resIds:
            dbN[resId] = db[resId]

        return dbN
    else:
        print "returning all"
        return db


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


def formatQuery(qry):
    res = None

    for filetype in qry:
        if res is not None:
            res += " <strong>AND</strong> "
        else:
            res = ""

        res += "<strong>%s</strong> :" % filetype

        for fieldname in qry[filetype]:
            qryValue = qry[filetype][fieldname]
            res += " %s = '<em>%s</em>'" % (fieldname, qryValue)

    if res is None:
        res = "<strong>All</strong>"

    return res




#DATABASE
def init_db(dbfile, indexfile):
    with app.app_context():
        print "initializing db"

        if not os.path.exists(dbfile):
            print "NO DATABASE FILE %s" % dbfile
            sys.exit(1)

        if not os.path.exists(indexfile):
            print "NO INDEX FILE %s" % indexfile
            sys.exit(1)

        global db
        global headers
        global queries

        jsonpickle.set_preferred_backend('simplejson')
        jsonpickle.set_encoder_options('simplejson', sort_keys=True, indent=1)
        dataDb = open(dbfile,    'r').read()
        dataIn = open(indexfile, 'r').read()


        db, lHeadersPos, lKeys = jsonpickle.decode(dataDb)
        headers                = jsonpickle.decode(dataIn)
        transcript.transcriptdata.headersPos, transcript.transcriptdata.keys = lHeadersPos, lKeys


        if db is None:
            print "no data in database"
            sys.exit(1)

        if len(db) == 0:
            print "database is empty"
            sys.exit(1)

        if headers is None:
            print "no data in index"
            sys.exit(1)

        if len(headers) == 0:
            print "index is empty"
            sys.exit(1)

        print "db loaded. %d entries" % len(db)


def getDb():
    if db is None:
        init_db(joiner.dbfile, joiner.indexfile)
    return [db, headers, queries]

if __name__ == '__main__':
    if not os.path.exists(joiner.dbfile) or not os.path.exists(joiner.indexfile):
        joiner.main()
    app.run(port=PORT)
