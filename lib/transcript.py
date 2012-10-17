import re,sys
import string
import decimal
import pprint
import math

graphWidth       = 600
graphHeight      = int(graphWidth / 2.16)


class transcriptdict(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    # Use dict directly, since super(dict, self) doesn't work. Not sure why, perhaps dict is not a new-style class.
    def __getitem__(self, key):
        key   = trimValue(key)
        if key not in self:
            self.__setitem__(key, None)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        key   = trimValue(key)
        if not isinstance(value, transcriptdata):
            value = transcriptdata(key)
        #print "setting item %s" % key
        return dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        return dict.__delitem__(self, trimValue(key))

    def __contains__(self, key):
        return dict.__contains__(self, trimValue(key))


class transcriptdata(object):
    headersPos = {}
    keys       = {}

    def __init__(self, gene):
        self.gene        = trimValue(gene)
        self.transcripts = {}
        self.fileTypes   = ['expression', 'exons', 'statistics']
        self.sampleNames = {}
        self.stats       = {}

        for fileType in self.fileTypes:
            if fileType not in self.headersPos:
                self.headersPos[fileType] = {}
            if fileType not in self.keys:
                self.keys[   fileType] = []

    def addKey(self, fileType, pos, key):
        if fileType in self.headersPos:
            if key not in self.headersPos[fileType]:
                while len (self.keys[   fileType]) <= pos:
                    self.keys[   fileType].append(None)

                if self.keys[   fileType][pos] is None:
                    print "        ADDING KEY %s: %d %s" % (fileType, pos, key)
                    self.keys[      fileType][pos] = key
                    self.headersPos[fileType][key] = pos
                else:
                    print "POSITION %d ALREADY TAKEN WHEN TRYING TO ADD %s to %d" % (pos, key, pos)
                    print self.keys[      fileType]
                    print self.headersPos[fileType]
                    raise KeyError
            else:
                print "KEY %s ALREADY ADDED" % key
                raise KeyError
        else:
            print "NO SUCH ORIGIN: %s" % fileType
            raise KeyError

    def getHeaderPos(self, fileType, key):
        if fileType in self.headersPos:
            if key in self.headersPos[fileType]:
                return self.headersPos[fileType][key]
            else:
                print "KEY %s DOES NOT EXISTS" % key
                print self.headersPos[fileType]
                raise KeyError
        else:
            print "NO SUCH ORIGIN: %s" % fileType
            raise KeyError

    def hasKey(self, fileType, key):
        if fileType in self.headersPos:
            if key in self.headersPos[fileType]:
                return True
            else:
                return False
        else:
            print "NO SUCH ORIGIN: %s" % fileType
            raise KeyError

    def addTranscript(self, transcript):
        #print "adding transcript: %s" % transcript
        transcript = trimValue(transcript)
        self.transcripts[transcript] = {}

    def append(self, transcript, fileType, regNum, sampleName, pos, val):
        regNum = str(regNum)
        if len(self.keys[fileType]) == 0:
            print "no keys defined for %s" % fileType
            print self.keys
            print self.keys[fileType]
            raise KeyError


        key  = self.keys[fileType][pos]
        transcript = trimValue(transcript)



        if transcript not in self.transcripts:
            #print "transcript %s not in %s" % (transcript, self.transcripts.keys())
            self.addTranscript(transcript)



        if fileType not in self.transcripts[transcript]:
            #print "  adding transcript %s fileType %s len %d" % (transcript, fileType, len(self.keys[fileType]))
            self.transcripts[transcript][fileType] = {}
        if regNum not in self.transcripts[transcript][fileType]:
            self.transcripts[transcript][fileType][regNum] = [None] * len(self.keys[fileType])



        if transcript not in self.sampleNames:
            self.sampleNames[transcript] = sampleName
        else:
            if sampleName != self.sampleNames[transcript]:
                print "TWO SOURCES FOR TRANSCRIPT? TRANSCRIPT %s ORIGIN %s SOURCE %s POS %d VAL %s" % (transcript, fileType, sampleName, pos, val)
                print self.sampleNames
                raise KeyError

        try:
            val = float(val) if '.' in val else int(val)
        except ValueError:
            try:
                val = decimal.Decimal(val)
            except decimal.InvalidOperation:
                pass



        #print self.transcripts[transcript]
        #print "appending gene %s: transcript %s sample %s file %s [#%03d] %s = %s" % (self.gene, transcript, sampleName, fileType, regNum, self.getHeader(fileType, pos), val)
        try:
            self.transcripts[transcript][fileType][regNum][pos] = val

        except KeyError, e:
            print "KEY ERROR: %s - TRANSCRIPT %s ORIGIN %s SOURCE %s POS %d VAL %s" % (e, transcript, fileType, sampleName, pos, val)
            print self.keys[fileType]
            print self.transcripts[transcript][fileType][regNum]
            raise

        except IndexError, e:
            print "INDEX ERROR: %s - TRANSCRIPT %s ORIGIN %s SOURCE %s POS %d VAL %s" % (e, transcript, fileType, sampleName, pos, val)
            print self.transcripts[transcript][fileType]
            print self.keys[fileType]
            raise

        self.updateStatistics()

    def getGene(self):
        return self.gene

    def getSampleName(self, transcript):
        if transcript in self.sampleNames:
            return self.sampleNames[transcript]
        else:
            print "NO SUCH TRANSCRIPT %s" % transcript
            raise KeyError

    def getSampleNames(self):
        sampleNames = []
        for transcript in self.getTranscripts():
            sampleName = self.getSampleName(transcript)
            if sampleName not in sampleNames:
                sampleNames.append(sampleName)
        sampleNames.sort()
        return sampleNames

    def getTranscripts(self):
        transcripts = self.transcripts.keys()
        transcripts.sort()
        return transcripts

    def getFileTypes(self, transcript):
        if transcript in self.getTranscripts():
            fileTypes = self.transcripts[transcript].keys()
            fileTypes.sort()
            return fileTypes
        else:
            raise KeyError

    def getHeaders(self, fileType):
        if fileType in self.headersPos:
            headersKeys = self.headersPos[fileType].keys()
            headersKeys.sort()
            return headersKeys
        else:
            raise KeyError

    def getHeader(self, fileType, pos):
        if fileType in self.headersPos:
            if len(self.keys[fileType]) > pos:
                if self.keys[fileType][pos] is not None:
                    return self.keys[fileType][pos]
                else:
                    print "POS %d HAS NO VALUE" % pos
                    print self.keys[fileType]
                    print self.keys[fileType][pos]
                    raise KeyError
            else:
                print "POS %d DOES NOT EXISTS" % pos
                print self.keys[fileType]
                raise KeyError
        else:
            print "NO SUCH ORIGIN: %s" % fileType
            raise KeyError

    def getRegNums(self, transcript, fileType):
        regNums = []
        if transcript in self.getTranscripts():
            if fileType in self.getFileTypes(transcript):
                for regNum in self.transcripts[transcript][fileType].keys():
                    if regNum not in regNums:
                        regNums.append(regNum)
        regNums.sort(key=int)
        return regNums

    def getValue(self, transcript, fileType, regNum, key):
        if transcript in self.getTranscripts():
            if fileType in self.getFileTypes(transcript):
                if regNum in self.getRegNums(transcript,fileType):
                    if key in self.getHeaders(fileType):
                        pos = self.getHeaderPos(fileType, key)
                        try:
                            val = self.transcripts[transcript][fileType][regNum][pos]
                            return val
                        except:
                            raise
                    else:
                        print "KEY %s DOES NOT EXISTS TO FILETYPE %s" % (key, fileType)
                        print self.headersPos[fileType]
                        raise KeyError
                else:
                    print "REG NUM %d DOES NOT EXISTS TO TRANSCRIPT %s FILETYPE %s" % (regNum, transcript, fileType)
                    print self.transcripts[transcript]
                    raise KeyError
            else:
                print "FILETYPE %s DOES NOT EXISTS TO TRANSCRIPT %s" % (fileType, transcript)
                print self.transcripts[transcript]
                raise KeyError
        else:
            print "TRANSCRIPT %s DOES NOT EXISTS" % (transcript)
            print self.transcripts
            raise KeyError

    def updateStatistics(self):
        sampleNames = self.getSampleNames()
        sampleNames.sort()
        if len(sampleNames) == 1:
            self.stats['category'] = sampleNames[0]
        else:
            self.stats['category'] = 'BOTH'


        maxFPKM        = None
        minFPKM        = None
        maxLeft        = None
        minLeft        = None
        maxRight       = None
        minRight       = None
        numTranscripts = len(self.getTranscripts())
        sampleFPKM     = {}

        for transcript in self.getTranscripts():
            #print "    TRANSCRIPT: %s (SAMPLE: %s)" % (transcript, self.getSampleName(transcript))

            sample = self.getSampleName(transcript)

            for fileType in ['expression']:
                #print "      ORIGIN %s:" % (fileType)

                for regNum in self.getRegNums(transcript, fileType):
                    #print "        #%03d:" % (regNum)

                    left  = self.getValue(transcript, fileType, regNum, 'left' )
                    right = self.getValue(transcript, fileType, regNum, 'right')
                    FPKM  = self.getValue(transcript, fileType, regNum, 'FPKM' )

                    if ((left is None) or (right is None) or (FPKM is None)):
                        continue

                    left  = left
                    right = right
                    FPKM  = FPKM
                    #print "          LEFT %s RIGHT %s FPKM %s" % (left, right, FPKM)


                    if (( FPKM  is None ) or ( FPKM  >= maxFPKM  )): maxFPKM  = FPKM
                    if (( FPKM  is None ) or ( FPKM  <= minFPKM  )): minFPKM  = FPKM
                    if (( left  is None ) or ( left  >= maxLeft  )): maxLeft  = left
                    if (( left  is None ) or ( left  <= minLeft  )): minLeft  = left
                    if (( right is None ) or ( right >= maxRight )): maxRight = right
                    if (( right is None ) or ( right <= minRight )): minRight = right

                    if sample not in sampleFPKM:
                        sampleFPKM[sample] =    {
                                                    'min': FPKM,
                                                    'max': FPKM
                                                }

                    if FPKM < sampleFPKM[sample]['min']: sampleFPKM[sample]['min'] = FPKM
                    if FPKM > sampleFPKM[sample]['max']: sampleFPKM[sample]['max'] = FPKM


        props       = [0]
        for sample1 in sampleFPKM:
            for sample2 in sampleFPKM:
                if sample1 == sample2: continue
                propMin = sampleFPKM[sample1]['min'] / sampleFPKM[sample2]['min']
                propMax = sampleFPKM[sample1]['max'] / sampleFPKM[sample2]['max']
                propVs  = sampleFPKM[sample1]['min'] / sampleFPKM[sample2]['max']
                props.extend([propMin, propMax, propVs])

        minFPKMprop = min(props)
        maxFPKMprop = max(props)

        self.stats['numTranscripts'] = numTranscripts
        if ((minFPKM     is not None) and (('minFPKM'     not in self.stats) or (minFPKM     < self.stats['minFPKM'       ]))): self.stats['minFPKM'       ] = minFPKM
        if ((maxFPKM     is not None) and (('maxFPKM'     not in self.stats) or (maxFPKM     > self.stats['maxFPKM'       ]))): self.stats['maxFPKM'       ] = maxFPKM
        if ((minFPKMprop is not None) and (('minFPKMprop' not in self.stats) or (minFPKMprop < self.stats['minFPKMprop'   ]))): self.stats['minFPKMprop'   ] = minFPKMprop
        if ((maxFPKMprop is not None) and (('maxFPKMprop' not in self.stats) or (maxFPKMprop > self.stats['maxFPKMprop'   ]))): self.stats['maxFPKMprop'   ] = maxFPKMprop
        if ((minLeft     is not None) and (('minBegin'    not in self.stats) or (minLeft     < self.stats['minBegin'      ]))): self.stats['minBegin'      ] = minLeft
        if ((maxRight    is not None) and (('maxEnd'      not in self.stats) or (maxRight    > self.stats['maxEnd'        ]))): self.stats['maxEnd'        ] = maxRight
        #if ((maxLeft     is not None) and (('maxLeft'     not in self.stats) or (maxLeft     > self.stats['maxLeft'       ]))): self.stats['maxLeft'       ] = maxLeft
        #if ((minRight    is not None) and (('minRight'    not in self.stats) or (minRight    < self.stats['minRight'      ]))): self.stats['minRight'      ] = minRight
        pass

    def getGraph(self):
        graphData = {}
        for transcript in self.getTranscripts():
            sampleName  = self.getSampleName(transcript)
            fileType    = 'expression'

            #for regNum in self.getRegNums(transcript, fileType):
                #exon_number = self.getValue(transcript, fileType, regNum, 'exon_number')
                #start       = self.getValue(transcript, fileType, regNum, 'start'      )
                #end         = self.getValue(transcript, fileType, regNum, 'end'        )
                #length      = self.getValue(transcript, fileType, regNum, 'length'     )
                #fpkm        = self.getValue(transcript, fileType, regNum, 'FPKM'       )
            sample      = self.getSampleName(transcript)

                #graphData[transcript]['start' ] = start
                #graphData[transcript]['end'   ] = end
                #graphData[transcript]['length'] = length
                #graphData[transcript]['FPKM'  ] = fpkm
            if transcript not in graphData:
                    graphData[transcript] = { }
            graphData[transcript]['sample'] = sample
            #pprint.pprint(graphData[transcript])


            if len(graphData) > 0:
                if 'DATA' not in graphData[transcript]:
                    graphData[transcript]['DATA'] = {}

                fileType    = 'exons'
                for regNum in self.getRegNums(transcript, fileType):
                    start         = self.getValue(transcript, fileType, regNum, 'start'       )
                    end           = self.getValue(transcript, fileType, regNum, 'end'         )
                    fpkm          = self.getValue(transcript, fileType, regNum, 'FPKM'        )
                    exon_number   = self.getValue(transcript, fileType, regNum, 'exon_number' )

                    if exon_number not in graphData[transcript]['DATA'  ]:
                        graphData[transcript]['DATA'  ][exon_number] = {}

                    graphData[transcript]['DATA'  ][exon_number]['start' ] = start
                    graphData[transcript]['DATA'  ][exon_number]['end'   ] = end
                    graphData[transcript]['DATA'  ][exon_number]['FPKM'  ] = fpkm

        if len(graphData) > 0:
            graphText = getGraphTag(self.gene, self.stats['category'], graphData)
            self.stats['graphText'] = graphText
        else:
            self.stats['graphText'] = 'NaN'

    def __repr__(self):
        try:
            resp = "\n  GENE: %s (TRANSCRIPTS: %02d - CATEGORY: %s)\n" % \
               (self.gene, len(self.getTranscripts()), self.stats['category'])
        except KeyError:
            print "STATS", self.stats
            raise

        for key in self.stats:
            resp += "    %s: %s\n" % (key.upper(), self.stats[key])

        resp += "    GRAPH: %s\n" % (self.getGraph())

        for transcript in self.getTranscripts():
            resp += "    TRANSCRIPT: %s (SAMPLE: %s)\n" % (transcript, self.getSampleName(transcript))

            for fileType in self.getFileTypes(transcript):
                resp += "      ORIGIN %s:\n" % (fileType)

                for regNum in self.getRegNums(transcript, fileType):
                    resp += "        #%03d:\n" % (int(regNum))

                    for key in self.getHeaders(fileType):
                        value = self.getValue(transcript, fileType, regNum, key)
                        resp += "          %s: %s\n" % (key.upper(), value)

        return resp


def getGraphTag(geneId, category, graphData):

    #graphData[transcriptId] = { 'left'  : transcript.getAttribute('left' ),
    #                            'right' : transcript.getAttribute('right'),
    #                            'length': transcript.getAttribute('length'),
    #                            'FPKM_1': transcript.getAttribute('FKPM_1'),
    #                            'FPKM_2': transcript.getAttribute('FKPM_2'),
    #                            'DATA'  : {
                                            #    exonName: {
                                            #        FPKM
                                            #        start
                                            #        end
                                            #    }
                                            #}
    #                            }
    #<transcripts>
    #        <transcript id=\"CUFF.11" Accession1=\"emb|AM486146.1|" Accession2=\"gb|AC172743.3|" Contig=\"NODE_1011_length_409_cov_123.496330" Contig_length=\"475" Description1=\"Vitis vinifera contig VV78X200411.3, whole genome shotgun sequence." Description2=\"Medicago truncatula chromosome 2 BAC clone mth2-26c15, complete sequence." FMI=\"1" FPKM_2=\"318.835" FPKM_conf_hi=\"351.721" FPKM_conf_lo=\"285.95" bundle_id=\"4709" coverage=\"85.5345" eval1=\"1e-82" eval2=\"2e-81" left=\"0" length=\"333" right=\"475" trans_id=\"CUFF.11\">
    #                <exon id=\"0" FPKM=\"318.8351742599" conf_hi=\"351.720512" conf_lo=\"285.949837" cov=\"85.534535" dot=\"." end=\"66"  exon_number=\"1" frame=\"+" gene_id=\"CUFF.11" program=\"Cufflinks" start=\"1"   thousand=\"1000" transcript_id=\"CUFF.11.1" type=\"exon"/>
    #                <exon id=\"1" FPKM=\"318.8351742599" conf_hi=\"351.720512" conf_lo=\"285.949837" cov=\"85.534535" dot=\"." end=\"475" exon_number=\"2" frame=\"+" gene_id=\"CUFF.11" program=\"Cufflinks" start=\"209" thousand=\"1000" transcript_id=\"CUFF.11.1" type=\"exon"/>

    #chxr=0,0,110 length
    #&chxt=y&chs=300x139 #size
    #&cht=lc #style
    #&chco=DA3B15,F7A10A #colors
    #&chds=0,100,0,100,0,100,0,100,0,100,0,100,0,100,-10.435,100 #axis sizes
    #&chd=s:abdegedbageba,somedabelprmnr #data
    #&chdl=transcript+1|transcript+2 #names
    #&chdlp=b
    #&chls=2,10,5|2,10,5 # line format

    maxFPKM        = -1
    minFPKM        = 99999999999
    maxLeft        = -1
    minLeft        = 99999999999
    maxRight       = -1
    minRight       = 99999999999
    numTranscripts = len(graphData.keys())

    #print str(graphData)
    chdL = {}
    for transcript in graphData.keys():
        data   = graphData[transcript]
        DATA   = data['DATA'  ]

        if not chdL.has_key(transcript):
            chdL[transcript] = {}

        chdL[transcript]['type'] = graphData[transcript]['sample']

        for exonName in DATA.keys():
            exonData  = DATA[exonName]
            exonFPKM  = float(exonData['FPKM' ])
            exonStart = int(  exonData['start'])
            exonEnd   = int(  exonData['end'  ])

            #print "TRANCRIPT %s EXON %s FPKM %d START %s END %s" % (transcript, exonName, exonFPKM, exonStart, exonEnd)
            if ( exonFPKM  > maxFPKM  ): maxFPKM  = exonFPKM
            if ( exonFPKM  < minFPKM  ): minFPKM  = exonFPKM
            if ( exonStart > maxLeft  ): maxLeft  = exonStart
            if ( exonStart < minLeft  ): minLeft  = exonStart
            if ( exonEnd   > maxRight ): maxRight = exonEnd
            if ( exonEnd   < minRight ): minRight = exonEnd


    #print "EXON FPKM MAX %d MIN %d" % (maxFPKM , minFPKM  )
    #print "LEFT      MAX %d MIN %d" % (maxLeft , minLeft  )
    #print "RIGHT     MAX %d MIN %d" % (maxRight, minRight )

    for transcript in graphData.keys():
        data      = graphData[transcript]
        DATA      = data['DATA'  ]

        pos       = { 'x': [], 'y': [] }

        lastStart = -1
        lastEnd   = -1
        for exonName in DATA.keys():
            exonData  = DATA[exonName]
            exonFPKM  = float(exonData['FPKM' ])
            exonStart = int(  exonData['start'])
            exonEnd   = int(  exonData['end'  ])


            if (len((pos['x'])) == 0) and (exonStart != 1):
                pos['x'].append(str(1            ))
                pos['y'].append(str(0            ))
                pos['x'].append(str(exonStart - 1))
                pos['y'].append(str(0            ))

            if lastEnd != -1 and lastEnd != exonStart:
                pos['x'].append(str(lastEnd   + 1))
                pos['y'].append(str(0            ))
                pos['x'].append(str(exonStart - 1))
                pos['y'].append(str(0            ))

            pos['x'].append(str(exonStart    ))
            pos['y'].append(str(int(exonFPKM)))

            pos['x'].append(str(exonEnd      ))
            pos['y'].append(str(int(exonFPKM)))

            lastStart = exonStart
            lastEnd   = exonEnd

            #print "      EXON START '%d' END '%d' FPKM '%d'" % (exonStart, exonEnd, exonFPKM)


        if (( lastEnd != -1 ) and (( lastEnd + 1 ) < maxRight )):
            pos['x'].append(str(lastEnd + 1))
            pos['y'].append(str(0          ))
            pos['x'].append(str(maxRight   ))
            pos['y'].append(str(0          ))
            #print "PADDING FOR LAST END '%d' MAX RIGHT '%d'" % (lastEnd, maxRight)
        else:
            #print "NOT PADDING FOR LAST END '%d' MAX RIGHT '%d'" % (lastEnd, maxRight)
            pass


        chdL[transcript]['data']  = ",".join(pos['x']) + "|"
        chdL[transcript]['data'] += ",".join(pos['y'])


    maxFPKMGraph = int(maxFPKM * 1.1)

    #colors=['DA3B15','F7A10A','FF9900','FF9900','FF9900','FF9900','FF9900','FF9900']
    colors   = ['FF0000','00FF00','0000FF','000000','AAAAAA','FFFF33','660099','FF9933']


    chds = "chds="  + ",".join(["0,%d" % (maxFPKMGraph) +""]*numTranscripts)


    chdl  = []
    chdLs = []
    chlsL = []
    chmL  = []
    chcoL = []
    cCount = 0
    for transcript in chdL.keys():
        geneType = chdL[transcript]['type']
        data     = chdL[transcript]['data']

        chdl.append("%s+(%s)" % (transcript, geneType))
        chdLs.append(data)

        chcoL.append(colors[cCount] + "AA")
        chmL.append("B,%s22,%d,0,0" % (colors[cCount], cCount))

        #TODO: FIX
        if   geneType == '1':
            chlsL.append("2,10,5")
        elif geneType == '2':
            chlsL.append("2")
        cCount += 1

    chco = "chco=%s"  % ",".join(chcoL)
    chm  = "chm=%s"   % "|".join(chmL )
    chls = "chls=%s"  % "|".join(chlsL)
    chd  = "chd=t:%s" % "|".join(chdLs)
    chdl = "chdl=%s"  % "|".join(chdl )

    apiString    = "chxr=0,%d,%s"                  % (int(minFPKM), maxFPKMGraph )
    apiString   += "|1,%d,%d"                      % (int(minLeft), int(maxRight))
    apiString   += "&chxt=y,x&chs=%dx%d&cht=lxy"   % (graphWidth,   graphHeight  )
    apiString   += "&chxs=0,676767,11.5,0,lt,676767|1,676767,11.5,0,lt,676767&"
    apiString   += "&".join([chco, chds, chls, chdl, chd, chm])
    apiString   += '&chdlp=b&chds=a&chtt=Coverage+%s+(%sbp)' % (geneId, maxRight)

    graphTag  = '<img src="http://chart.apis.google.com/chart?%s' % apiString
    graphTag += '" width="%d" height="%d" alt="Coverage %s" />'   % ( graphWidth, graphHeight, geneId )

    return graphTag


def trimValue(value):
    return re.sub(r'(CUFF\.\d+)\.\d+', r'\1', value)


def corrAll(value):
    return value


def corrMinmax(value):
    minVal = min(value)
    maxVal = max(value)

    try:
        minVal = int(float(minVal))
    except ValueError:
        print "MIN VAL", minVal
        pass
    except TypeError:
        print "MIN VAL", minVal
        sys.exit(1)

    try:
        maxVal = int(float(maxVal)) + 1
    except ValueError:
        print "MAX VAL", maxVal
        pass
    except TypeError:
        print "MAX VAL", maxVal
        sys.exit(1)

    return [minVal, maxVal]


def corrNone(value):
    return []


def sortNode(key):
    #NODE_1_length_981_cov_40.408768
    #NODE_100_length_603_cov_73.814262
    vals = key.split("_")
    return int(vals[1])


def sort0(key):
    return key[0]





#'select'
#'rangemin'
#'rangeminmax'
#'input'

class index(object):
    def __init__(self):
        pass
    def __repr__(self):
        if hasattr(self, 'res'):
            return str(self.res)
        else:
            return super


def consolidate(val):
    seen = {}
    res  = []
    for x in val:
        if x[0] not in seen:
            #print "x0",x[0],"not yet seen. adding",x[1]
            seen[x[0]] = len(res)
            res.append([ x[0], [x[1][0]] ])
        else:
            pos = seen[x[0]]
            if x[1][0] not in res[ pos ][1]:
                #print "x0",x[0],"already seen at",pos,". appending",x[1]
                res[ pos ][1].append(x[1][0])
            else:
                #print "x0",x[0],"already seen at",pos,". skipping.",x[1],"already in"
                pass
    ind = index()
    ind.res = res
    return ind

def addHeader(headers, gene, fileType, key, value):
    if value is not None:
        if fileType not in headers:
            headers[fileType] = {}

        if key not in headers[fileType]:
            headers[fileType][key] = []

        headers[fileType][key].append( [ value, [ gene ] ] )

def getIndex(datas):

    headers = {}

    for gene in datas:
        data     = datas[gene]
        category = data.stats['category']
        addHeader(headers, gene, 'statistics', 'category', data.stats['category'])

        try:
            if "minFPKM"     in data.stats: addHeader(headers, gene, 'statistics', "FPKM"        , data.stats["minFPKM"    ])
            if "maxFPKM"     in data.stats: addHeader(headers, gene, 'statistics', "FPKM"        , data.stats["maxFPKM"    ])
            if "minFPKMprop" in data.stats: addHeader(headers, gene, 'statistics', "FPKMprop"    , data.stats["minFPKMprop"])
            if "maxFPKMprop" in data.stats: addHeader(headers, gene, 'statistics', "FPKMprop"    , data.stats["maxFPKMprop"])
            if "minBegin"    in data.stats: addHeader(headers, gene, 'statistics', "StartEnd"    , data.stats["minBegin"   ])
            if "maxEnd"      in data.stats: addHeader(headers, gene, 'statistics', "StartEnd"    , data.stats["maxEnd"     ])
        except KeyError:
            pprint.pprint(data.stats)
            raise

        for key in data.stats:
            statsKey = data.stats[key]

        for transcript in data.getTranscripts():
            sample = data.getSampleName(transcript)

            for fileType in data.getFileTypes(transcript):

                for regNum in data.getRegNums(transcript, fileType):

                    for key in data.getHeaders(fileType):
                        value = data.getValue(transcript, fileType, regNum, key)
                        addHeader(headers, gene, fileType, key, value)


    keysN = {}
    for filetype in headers:
        cols  = headers[filetype]

        if filetype not in translate:
            keysN[filetype] = cols
            continue

        if filetype not in keysN:
            keysN[filetype] = {}

        for colName in cols:
            val  = cols[colName]
            data = list(set([ x[0] for x in val ]))
            data.sort()
            #print val
            consolidated  = consolidate(val)
            cols[colName] = consolidated
            #print consolidated

            if colName in translate[filetype]:
                colNameNew, parsers, fieldType = translate[filetype][colName]

                if colNameNew is not None:
                    valN = data
                    for parser in parsers:
                        valN = parser(valN)

                    if ((fieldType == 'select') and (len(valN) == 1)):
                        continue

                    if fieldType == 'rangemin' or fieldType == 'rangeminmax' :
                        v1 = valN[0]
                        if v1 == 0: v1 = 1
                        v2 = valN[1]
                        try:
                            print "V1 %d (%d) V2 %d (%d)" % ( v1, math.log10(v1), v2, math.log10(v2) )
                            if (math.log10(v1) + 2) <= math.log10(v2):
                                print "  converting to log"
                                if  fieldType == 'rangemin':
                                    fieldType = 'rangeminlog'
                                elif fieldType == 'rangeminmax' :
                                    fieldType = 'rangeminmaxlog'
                        except ValueError:
                            print "value error: %s" % str(valN)
                            pass

                    keysN[filetype][colNameNew] = [valN, fieldType, consolidated]
            else:
                keysN[filetype][colName] = [data, 'select', consolidated]

    return keysN




translate = {
        #filetype
        #   column name        new name           correction type  fieldtype
        'statistics': {
            'category'      : [ 'Category',            [ corrAll    ], 'selectmultiple' ],

            "StartEnd"      : [ None,                  [ corrNone   ], 'rangeminmax'    ],
            "FPKM"          : [ 'Expression Level',    [ corrMinmax ], 'rangeminmax'    ],
            "FPKMprop"      : [ 'Expression Folds',    [ corrMinmax ], 'rangeminmax'    ],

            #'numTranscripts': [ 'Num Transcripts',     [ corrAll    ], 'select'   ],
            #"Start"         : [ "minLeft",             [ corrMinmax ], 'rangemin' ],
            #"End"           : [ "maxRight",            [ corrMinmax ], 'rangemin' ],
            #"minFPKM"       : [ "minFPKM",             [ corrMinmax ], 'rangemin' ],
            #"maxFPKM"       : [ "maxFPKM",             [ corrMinmax ], 'rangemin' ],
            #"minFPKMprop"   : [ "minFPKMprop",         [ corrMinmax ], 'rangemin' ],
            #"maxFPKMprop"   : [ "maxFPKMprop",         [ corrMinmax ], 'rangemin' ],

            #'minFPKM'       : [ 'Min FPKM',            [ corrMinmax ], 'rangemin' ],
            #'maxFPKM'       : [ 'Max FPKM',            [ corrMinmax ], 'rangemin' ],
            #'minLeft'       : [ 'Min Start',           [ corrMinmax ], 'rangemin' ],
            #'maxLeft'       : [ 'Max Start',           [ corrMinmax ], 'rangemin' ],
            #'minRight'      : [ 'Min End',             [ corrMinmax ], 'rangemin' ],
            #'maxRight'      : [ 'Max End',             [ corrMinmax ], 'rangemin' ],
            #'minFPKMprop'   : [ 'Min Exp. Level Diff', [ corrMinmax ], 'rangemin' ],
            #'maxFPKMprop'   : [ 'Max Exp. Level Diff', [ corrMinmax ], 'rangemin' ],
        },
        'expression': {
            'chr'           : [ None,                  [ corrNone   ], 'input'          ],
            'trans_id'      : [ 'Transcript ID',       [ corrNone   ], 'input'          ],
            'bundle_id'     : [ 'Bundle ID',           [ corrNone   ], 'input'          ],
            'left'          : [ None,                  [ corrMinmax ], 'rangemin'       ],
            'right'         : [ None,                  [ corrMinmax ], 'rangemin'       ],
            'FPKM'          : [ 'Expression Level',    [ corrMinmax ], 'rangemin'       ],
            'FMI'           : [ None,                  [ corrNone   ], 'select'         ],
            'frac'          : [ None,                  [ corrNone   ], 'rangemin'       ],
            'FPKM_conf_lo'  : [ 'Confidence Low',      [ corrMinmax ], 'rangemin'       ],
            'FPKM_conf_hi'  : [ 'Confidence High',     [ corrMinmax ], 'rangemin'       ],
            'coverage'      : [ 'Coverage',            [ corrMinmax ], 'rangemin'       ],
            'length'        : [ 'Length',              [ corrMinmax ], 'rangemin'       ],
            'Contig'        : [ 'Contig Name',         [ corrNone   ], 'input'          ],
            'Contig_length' : [ 'Contig Length',       [ corrMinmax ], 'rangemin'       ],
            'Accession1'    : [ 'Hit 1 Accession',     [ corrNone   ], 'input'          ],
            'Description1'  : [ 'Hit 1 Description',   [ corrNone   ], 'input'          ],
            'eval1'         : [ 'Hit 1 evalue',        [ corrMinmax ], 'rangemin'       ],
            'Accession2'    : [ 'Hit 2 Accession',     [ corrNone   ], 'input'          ],
            'Description2'  : [ 'Hit 2 Description',   [ corrNone   ], 'input'          ],
            'eval2'         : [ 'Hit 2 evalue',        [ corrMinmax ], 'rangemin'       ],
        },
        'exons': {
            'chr'           : [ None,                  [ corrNone   ], 'input'          ],
            'program'       : [ None,                  [ corrAll    ], 'select'         ],
            'type'          : [ None,                  [ corrAll    ], 'select'         ],
            'start'         : [ None,                  [ corrMinmax ], 'rangemin'       ],
            'end'           : [ None,                  [ corrMinmax ], 'rangemin'       ],
            'thousand'      : [ None,                  [ corrNone   ], None             ],
            'frame'         : [ 'Frame',               [ corrAll    ], 'selectmultiple' ],
            'dot'           : [ None,                  [ corrNone   ], None             ],
            'details'       : [ None,                  [ corrNone   ], None             ],
            'gene_id'       : [ None,                  [ corrNone   ], 'input'          ],
            'transcript_id' : [ 'Exon ID',             [ corrNone   ], 'input'          ],
            'exon_number'   : [ 'Exon Number',         [ corrAll    ], 'selectmultiple' ],
            'FPKM'          : [ 'Expression Level',    [ corrMinmax ], 'rangemin'       ],
            'frac'          : [ None,                  [ corrMinmax ], 'rangemin'       ],
            'conf_lo'       : [ 'Confidence Low',      [ corrMinmax ], 'rangemin'       ],
            'conf_hi'       : [ 'Confidence High',     [ corrMinmax ], 'rangemin'       ],
            'cov'           : [ 'Coverage',            [ corrMinmax ], 'rangemin'       ],
        }
}
