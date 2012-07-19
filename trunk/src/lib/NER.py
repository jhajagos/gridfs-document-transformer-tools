'''
Created on May 1, 2012

@author: Som Satapathy
'''
import nltk

class NER(object):

             
        def __init__(self):
                '''
                Constructor
                '''                
                 
        def generate_named_entities(self, rawText, ne_file):
                sentences = nltk.sent_tokenize(rawText)
                tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
                tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_sentences]
                chunked_sentences = nltk.batch_ne_chunk(tagged_sentences, binary=True)
                
                def extract_entity_names(t):
                        entity_names = []
                        
                        if hasattr(t, 'node') and t.node:
                                if t.node == 'NE':
                                        entity_names.append(' '.join([child[0] for child in t]))
                                else:
                                        for child in t:
                                                entity_names.extend(extract_entity_names(child))
                                                
                        return entity_names
                
                entity_names = []
                for tree in chunked_sentences:
                        # Print results per sentence
                        # print extract_entity_names(tree)
                        
                        entity_names.extend(extract_entity_names(tree))
                
                # Print all entity names
                #print entity_names

                #Unique named entities
                #named_entities = set(entity_names)
                #writeNER(named_entities, ne_file)                        
                
                # Named entity cloud
                namedEntityHash = dict()
                for entity_name in entity_names:
                        if namedEntityHash.has_key(entity_name):
                                namedEntityHash[entity_name] += 1
                        else:
                                namedEntityHash[entity_name] = 1 
                                
                if len(namedEntityHash) > 0:
                        result = sorted(namedEntityHash.iteritems(), key = lambda (k, v) : (v, k), reverse=True)
                        bestResults = result[:10]
                        bestResultsAscending = sorted(bestResults, key = lambda (k, v) : (v, k))
                        ranges=getRanges(bestResultsAscending)
                        writeNERCloud(bestResultsAscending, ranges, ne_file) 
                        
                                                        
def writeNERCloud(taglist, ranges, outputfile):
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
    outputf.write("<legend>Named Entity Cloud:</legend>\n")
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
        
def writeNER(entity_names, outputfile):
    outputf = open(outputfile, 'w')
    outputf.write("<style type=\"text/css\">\n")
    outputf.write(".largeTag {font-size: large;}\n")
    outputf.write("</style>\n")
    outputf.write("<form action='' style='width:200px;'>\n")
    outputf.write("<fieldset>\n")
    outputf.write("<legend>Named Entities:</legend>\n")
    rangeStyle = ["largeTag"]
    
    for entity_name in entity_names:
        rangeIndex = 0
        outputf.write("<span class=\"" + rangeStyle[rangeIndex] + "\">" + entity_name + "</a></span> ")

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