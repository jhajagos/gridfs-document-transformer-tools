'''
Created on May 1, 2012

@author: Som Satapathy
'''

class WordCloud(object):
        def __init__(self, minWordLen = 4):
                """
                Default initializer
                """
                self.wordsHash = dict()
                self.minWordLength = minWordLen
                self.illegalSymbols = { '.', ',', ';', '?', '<', '>', '[', ']', '(', ')', '{', '}', '`', '~', '!' }

        def addWords(self, wordOrSentence):
                """
                Method will populate engine with words.
                """
                wLines = wordOrSentence.split(' ')
                for line in wLines:
                        for isy in self.illegalSymbols:
                                line = line.replace(isy, '')
                        line = line.strip().lower()

                        if len(line) > self.minWordLength:
                                if self.wordsHash.has_key(line):
                                        self.wordsHash[line] += 1
                                else:
                                        self.wordsHash[line] = 1

        def cloud(self, wc_file):
                """
                Method will create a word cloud html of words listed by popularity and ordered alphabetically
                """
                if len(self.wordsHash) > 0:
                        result = sorted(self.wordsHash.iteritems(), key = lambda (k, v) : (v, k), reverse=True)
                        bestResults = result[:10]
                        bestResultsAscending = sorted(bestResults, key = lambda (k, v) : (v, k))
                        ranges=getRanges(bestResultsAscending)
                        writeCloud(bestResultsAscending, ranges, wc_file)
                return None

        def total_words_count(self):
                return len(self.wordsHash)

        def reset(self):
                self.totalWordsCount = 0
                self.wordsHash.clear()
                
def writeCloud(taglist, ranges, outputfile):
    outputf = open(outputfile, 'w')
    outputf.write("<style type=\"text/css\">\n")
    outputf.write(".smallestTag {font-size: xx-small;}\n")
    outputf.write(".smallTag {font-size: small;}\n")
    outputf.write(".mediumTag {font-size: medium;}\n")
    outputf.write(".largeTag {font-size: large;}\n")
    outputf.write(".largestTag {font-size: xx-large;}\n")
    outputf.write("</style>\n")
    outputf.write("<form action='' style='width:200px;'>\n")
    outputf.write("<fieldset>\n")
    outputf.write("<legend>Word Cloud:</legend>\n")
    rangeStyle = ["smallestTag", "smallTag", "mediumTag", "largeTag", "largestTag"]
    # resort the tags alphabetically
    taglist.sort(lambda x, y: cmp(x[0], y[0]))
    for tag in taglist:
        rangeIndex = 0
        for range in ranges:
            if (tag[1] >= range[0] and tag[1] <= range[1]):
                outputf.write("<span class=\"" + rangeStyle[rangeIndex] + "\">" + tag[0] + "</a></span> ")
                break
            rangeIndex = rangeIndex + 1
    outputf.write("</fieldset>\n")
    outputf.write("</form>\n")            
    outputf.close()                
                
def getRanges(taglist):
    mincount = taglist[0][1]
    maxcount = taglist[len(taglist) - 1][1]
    distrib = float(maxcount - mincount) / 4;
    index = mincount
    ranges = []
    while (index <= maxcount):
        range = (index, index + distrib)
        index = index + distrib
        ranges.append(range)
    return ranges                