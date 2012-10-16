#!/usr/bin/python
import sys,os
import re
import pprint

sys.path.append('lib')
import simplejson
import jsonpickle
import transcript

indexTab1        = 2 #chr
indexTab2        = 0 #transc
indexGtf1        = 0 #chr
indexGtf2        = 9 #transc

base             = '../Analysis/Analysis/Expression'
expressionName   = "transcripts_annotated.expr.csv"
gtfName          = "transcripts.gtf"
inputAnnoTabFile = "rnaSeq/input/ANNO.tab"
dbfile           = 'db.json'


#if os.path.exists(inputAnnoTabFile):
    #my $annoFile  = readTab->new(inTabFile => $inputAnnoTabFile,   firstLine => 1);
    #my %annoSetup = (
    #    inTable       => $annoFile,
    #    primaryColumn => 'queryId'
    #);
    #my $anno = anno->new(%annoSetup);
    #die if ! defined $anno;
    #pass

def main():
    dataset  = {}
    outfiles = {}
    datas    = transcript.transcriptdict()
    namesA   = [ x[0] for x in transcript.sampleFolders ]
    namesA.sort()

    #for ext in ( 'tab', 'csv'):
    #    outfiles[ext] = {
    #                        "all"  : {},
    #                        "1"    : {},
    #                        "1only": {},
    #                        "2"    : {},
    #                        "2only": {},
    #                        "1and2": {},
    #                    }
    #
    #    outfiles[ext]["all"  ]['filename'] = "transcripts_annotated_expr.%s"        % ext
    #    outfiles[ext]["1"    ]['filename'] = "transcripts_annotated_expr%s.%s"      % (namesA[0],            ext)
    #    outfiles[ext]["1only"]['filename'] = "transcripts_annotated_expr%sonly.%s"  % (namesA[0],            ext)
    #    outfiles[ext]["2"    ]['filename'] = "transcripts_annotated_expr%s.%s"      % (namesA[1],            ext)
    #    outfiles[ext]["2only"]['filename'] = "transcripts_annotated_expr%sonly.%s"  % (namesA[1],            ext)
    #    outfiles[ext]["1and2"]['filename'] = "transcripts_annotated_expr%sand%s.%s" % (namesA[0], namesA[1], ext)
    #
    #    for group in outfiles[ext]:
    #        fn = outfiles[ext][group]['filename']
    #        outfiles[ext][group]['filehandle'] = open(fn, 'w')


    for sampleFolder in transcript.sampleFolders:
        sampleName, sampleDirectory = sampleFolder
        dataset[sampleName] = {
            'expression' : os.path.join(base, sampleDirectory, expressionName),
            'exons'      : os.path.join(base, sampleDirectory, gtfName       ),
            'name'       : sampleName,
         }

        expfile = dataset[sampleName]['expression' ]
        gtffile = dataset[sampleName]['exons'      ]

        loadExpFile(expfile, sampleName, datas)
        loadGtfFile(gtffile, sampleName, datas)

    #pprint.pprint(datas)
    jsonpickle.set_preferred_backend('simplejson')
    jsonpickle.set_encoder_options('simplejson', sort_keys=True, indent=1)
    jsonp = jsonpickle.encode([datas, transcript.translateHeader(transcript.transcriptdata.headers), transcript.transcriptdata.headers, transcript.transcriptdata.headersPos, transcript.transcriptdata.keys])
    #print jsonp
    with open(dbfile, 'w') as f:
        f.write(jsonp)

def loadExpFile(filename, sampleName, keyHash):
    #trans_id    bundle_id    chr    left    right    FPKM    FMI    frac    FPKM_conf_lo    FPKM_conf_hi    coverage    length    Contig    Contig_length    Accession1    Description1    eval1    Accession2    Description2    eval2
    #CUFF.1085.1    4733    NODE_1_length_981_cov_40.408768    0    1047    956.781    1    1    927.824    985.738    316.952    1047    NODE_1_length_981_cov_40.408768    1047    dbj|AK245806.1|        1e-164    gb|AC145222.18|    Medicago truncatula clone mth2-29a15, complete sequence.    1e-116
    #CUFF.18.1    3569    NODE_100_length_603_cov_73.814262    0    664    1698.67    1    1    1650.22    1747.12    562.723    664    NODE_100_length_603_cov_73.814262    669    gb|BT098464.1|    Soybean clone JCVI-FLGm-23M11 unknown mRNA.    1e-95    ref|XM_002273715.1|    PREDICTED: Vitis vinifera hypothetical protein LOC100262670 (LOC100262670), mRNA.    3e-44

    print "    READING FILE %s" % filename
    print "      KEYHASH ",len(keyHash)

    header   = {}
    regNum   = 0
    with open(filename, 'r') as fd:
        for line in fd:
            line = line.strip()
            #$l =~ s/\r//g;

            F        = line.split("\t")
            gene     = F[indexTab1]
            transcript     = F[indexTab2]

            if F[0] == "chr" or F[0] == "trans_id":
                for c in range(0, len(F)):
                    #print "%d -> %s\t" % (c, F[c])
                    header[F[c]] = c
                continue

            if header is not None:
                for name in header:
                    pos = header[name]
                    if not keyHash[gene].hasKey('expression', name):
                        keyHash[gene].addKey('expression', pos, name)
                header = None

            regNum += 1
            for c in range(0, len(F)):
                val    = F[c]
                #print "GENE %-40s TRANSCRIPT %-5s  KEY %d VAL %s" % (gene, transcript, c, val)
                keyHash[gene].append(transcript, 'expression', regNum, sampleName, c, val)

    print "      KEYHASH ",len(keyHash)
    print "    FILE %s READ" % filename

def loadGtfFile(filename, sampleName, keyHash):
    print "    READING FILE %s" % filename
    print "      KEYHASH ",len(keyHash)


    #chd                                    program         type            start   end     thousand frame  dot    details
    #0                                      1               2               3       4       5       6       7      8
    #NODE_1011_length_409_cov_123.496330    Cufflinks    transcript    1    475    1000    +    .    gene_id "CUFF.31"; transcript_id "CUFF.31.1"; FPKM "3746.7157373742"; frac "1.000000"; conf_lo "3645.109303"; conf_hi "3848.322172"; cov "1237.867868";
    #NODE_1011_length_409_cov_123.496330    Cufflinks    exon            1    66    1000    +    .    gene_id "CUFF.31"; transcript_id "CUFF.31.1"; exon_number "1"; FPKM "3746.7157373742"; frac "1.000000"; conf_lo "3645.109303"; conf_hi "3848.322172"; cov "1237.867868";
    #NODE_1011_length_409_cov_123.496330    Cufflinks    exon            209    475    1000    +    .    gene_id "CUFF.31"; transcript_id "CUFF.31.1"; exon_number "2"; FPKM "3746.7157373742"; frac "1.000000"; conf_lo "3645.109303"; conf_hi "3848.322172"; cov "1237.867868";
    #NODE_1011_length_409_cov_123.496330    Cufflinks    transcript    67    208    1000    .    .    gene_id "CUFF.33"; transcript_id "CUFF.33.1"; FPKM "2295.5230221941"; frac "1.000000"; conf_lo "2173.732187"; conf_hi "2417.313858"; cov "760.338519";
    #NODE_1011_length_409_cov_123.496330    Cufflinks    exon            67    208    1000    .    .    gene_id "CUFF.33"; transcript_id "CUFF.33.1"; exon_number "1"; FPKM "2295.5230221941"; frac "1.000000"; conf_lo "2173.732187"; conf_hi "2417.313858"; cov "760.338519";


    regNum     = 0
    lastColPos = 0
    with open(filename, 'r') as fd:
        for line in fd:
            line       = line.strip()

            F = line.split("\t")

            if F[2] == 'transcript': continue
            regNum += 1
            gene   = F[indexGtf1]

            if regNum == 1:
                #print line
                for pos, name in enumerate(['chr'    , 'program'      , 'type',
                                            'start'  , 'end'          , 'thousand',
                                            'frame'  , 'dot'          , 'details',
                                            'gene_id', 'transcript_id', 'exon_number',
                                            'FPKM'   , 'frac'         , 'conf_lo',
                                            'conf_hi', 'cov'
                                            ]):
                    if not keyHash[gene].hasKey('exons', name):
                        keyHash[gene].addKey('exons', pos, name)
                    lastColPos = pos

            details = F[keyHash[gene].getHeaderPos('exons', "details")].split(';')

            for col in details:
                #print "COL '%s'" % col,
                cmatch = re.match('\s*(\S+)\s+\"(.+?)\"\s*', col)
                if cmatch is not None:
                    name   = cmatch.group(1)
                    val    = cmatch.group(2)

                    if val is None: val = ''
                    #print " NAME '%s' VAL '%s'" % (name, val),

                    if not keyHash[gene].hasKey('exons', name):
                        lastColPos += 1
                        if not keyHash[gene].hasKey('exons', F[lastColPos]):
                            keyHash[gene].addKey( 'exons', lastColPos, name)
                        #keyHash[gene].headers['exons'][name] = len(keyHash[gene].keys['exons'])
                        #keyHash[gene].keys[   'exons'].append(name)
                        #pos = keyHash[gene].headers['exons'][name]

                    while F <= lastColPos:
                        F.append(None)

                    F.insert(lastColPos, val)
                    #print " NUMBER %d" % (number),

            transcript    = F[indexGtf2]

            for pos in range(0, len(F)):
                val = F[pos]
                key = keyHash[gene].getHeader('exons', pos)
                #print "GENE %-40s TRANSCRIPT %-5s  KEY %-13s VAL %s" % (gene, transcript, key, val)
                keyHash[gene].append(transcript, 'exons', regNum, sampleName, pos, val)


    print "      KEYHASH ",len(keyHash)
    print "    FILE %s READ" % filename

if __name__ == '__main__': main()
