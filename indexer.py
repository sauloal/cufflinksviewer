#!/usr/bin/python
import sys,os
import re
import pprint

sys.path.append('lib')
import simplejson
import jsonpickle
import transcript
import joiner

setupfile        = joiner.setupfile
if not os.path.exists(setupfile):
        print "count not find setup file %s" % setupfile
        sys.exit(1)

for k,v in jsonpickle.decode(open(setupfile, 'r').read())['joiner'].items():
        globals()[k] = v

indexfile = joiner.indexfile


def main():
    jsonpickle.set_preferred_backend('simplejson')
    jsonpickle.set_encoder_options('simplejson', sort_keys=True, indent=1)

    print "loading data %s" % dbfile    
    datas, transcript.transcriptdata.headersPos, transcript.transcriptdata.keys = jsonpickle.decode(open(dbfile, 'r').read())

    print "creating index %s" % indexfile
    jsonq = jsonpickle.encode(transcript.getIndex(datas))
    with open(indexfile, 'w') as f:
        f.write(jsonq)

if __name__ == "__main__": main()
