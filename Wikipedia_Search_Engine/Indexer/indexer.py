import xml.etree.ElementTree as et
# import xml.sax.handler
from bz2file import BZ2File
from sortedcontainers import SortedDict
from collections import Counter, defaultdict
import re
import nltk
import string
from nltk.stem import WordNetLemmatizer
from Stemmer import Stemmer
from nltk.corpus import stopwords as nltk_stopwords
import time
import sys

prefix = '{http://www.mediawiki.org/xml/export-0.10/}'
page_dict = {}
words_dict = SortedDict({})  #defaultdict(list)
try_till = None
stopwords = list(nltk_stopwords.words('english'))
url_stopwords = ["www", "com", "http", "https", "net", "org", "html", "ftp", "archives", "pdf", "jpg", "jpeg", "gif", "png", "txt", "redirect"]
punctuations = list(string.punctuation) + ['_', '\t', '\n']
digits = [str(x) for x in range(10)]
max_wordlen = 20
min_wordlen = 3
use_lematizer = False
output_dir = "."
stemmer = Stemmer('english')
lemmatizer = WordNetLemmatizer()
file_count = 692
write_after = 1000000
docid = 0
curpage_counts = {}

def is_english(word):
    try:
        str(word).encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True

def tokenize(data, istitle=False):
    global min_wordlen, max_wordlen
    good_tokens = []
    rpun = '[' + re.escape(''.join(punctuations)) + ']'
    data = re.sub(rpun, ' ', data.strip())  ## remove punctuations/symbols and split words using them
    if not istitle:
        data = re.sub(r'\w*\d\w*', '', data).strip()  ## omit words having digits in them if not in title
    tokens = data.strip().split()  ## splitting into words
    for t in tokens:
        if len(str(t))>=min_wordlen and len(str(t))<max_wordlen and is_english(t):
            good_tokens.append(t)
    return good_tokens

def remove_stopwords(words):
    good_words = []
    for w in words:
        if w in stopwords or w in url_stopwords:
            continue
        good_words.append(w)
    return good_words

def process_words(words,lem):
    global min_wordlen, max_wordlen
    words = remove_stopwords(words)
    words = [stemmer.stemWord(w) for w in words]
    if lem:
        words = [lemmatizer.lemmatize(w) for w in words] 
    words = [w for w in words if len(w)>=min_wordlen and len(w)<max_wordlen]
    return words

def process_text(content,ctype):
    global use_lematizer
    content = content.lower()  ## casefolding
    if ctype=='title':
        tokens = tokenize(content,True)
        words = process_words(tokens,use_lematizer)
        return words
    if ctype=='body':
        text, categories, links, info = get_sections(content)
        text = tokenize(text)
        text = process_words(text,use_lematizer)
        categories = tokenize(categories)
        categories = process_words(categories,use_lematizer)
        links = tokenize(links)
        links = process_words(links,use_lematizer)
        info = tokenize(info)
        info = process_words(info,use_lematizer)
        return text, categories, links, info


def get_sections(content) :
    text, categories, links, info = "", "", "", ""
    lines = content.split('\n')
    i = 0
    n = len(lines)
    while i < n:
        # print(lines[i], type(lines[i]))
        if "[[category" in lines[i]:
            line = lines[i].split("[[category:")
            if len(line)>1:
                categories += " "+line[1].split(']]')[0]
        elif "{{infobox" in lines[i]:
            # print(lines[i].split("{{Infobox")[1])
            info += " "+lines[i].split("{{infobox")[1]
            i += 1
            while i < n and '=' in lines[i]:
                info += " "+lines[i].split('=')[1]
                i += 1
        elif "==external links==" in lines[i]:
            links += " "+lines[i].split("==external links==")[1]
            i += 1
            syms = ['* [', '*[', '*{{', '* {{', 'http']
            rsym = '[' + re.escape(''.join(syms)) + ']'
            while i < n and ('* [' in lines[i] or '*[' in lines[i] or 'http' in lines[i] or '* {{' in lines[i]):
                links += " "+lines[i]
                i += 1
        else:
            text += " "+lines[i]
        i += 1
    return text, categories, links, info

def write_title_index():
    global page_dict, output_dir
    with open(output_dir+'/title_index.txt', 'a') as f:
        for key in page_dict:
            f.write(str(key)+"|"+page_dict[key][0]+"|"+page_dict[key][1]+"\n")

def write_intermediate_index(file_num):
    global words_dict, output_dir
    with open(output_dir+'/index'+str(file_num)+'.txt', 'w') as f:
        for w,cl in words_dict.items():
            cur_line = w
            for c in cl:
                cur_line = cur_line + '|' + c
            f.write(cur_line+'\n')
    with open(output_dir+'/meta_index.txt', 'a') as m:
        m.write(str(file_num)+' '+str(len(words_dict))+'\n')
    print("dumped",file_num)

def parseXML(context):
    global page_dict, try_till, write_after, words_dict, file_count, curpage_counts, docid
    for event, elem in context:
        if elem.tag == prefix+"title":
            ## Uncomment this if you need to continue prcessing after a break
            # if docid <= 3780932:
            #     continue
            page_dict[docid] = ["-","0"]
            # print("title",elem.text)
            if not elem.text:
                continue
            page_dict[docid][0] = elem.text
            cur_words = process_text(elem.text,'title')
            for w,c in Counter(cur_words).items():
                curpage_counts[w] = str(docid)+";t"+str(c)
        elif elem.tag == prefix+"text":
            ## Uncomment this if you need to continue prcessing after a break
            # if docid <= 3780932:
            #     continue
            if not elem.text:
                continue
            text, categories, links, info = process_text(elem.text,'body')
            ## text words
            for w,c in Counter(text).items():
                if w not in curpage_counts:
                    curpage_counts[w] = str(docid)+";b"+str(c)
                else:
                    curpage_counts[w] += ";b"+str(c)
            ## category words
            for w,c in Counter(categories).items():
                if w not in curpage_counts:
                    curpage_counts[w] = str(docid)+";c"+str(c)
                else:
                    curpage_counts[w] += ";c"+str(c)
            ## links words
            for w,c in Counter(links).items():
                if w not in curpage_counts:
                    curpage_counts[w] = str(docid)+";l"+str(c)
                else:
                    curpage_counts[w] += ";l"+str(c)
            ## info words
            for w,c in Counter(info).items():
                if w not in curpage_counts:
                    curpage_counts[w] = str(docid)+";i"+str(c)
                else:
                    curpage_counts[w] += ";i"+str(c)
            body_count = len(text) + len(categories) + len(links) + len(info)
            page_dict[docid][1] = str(body_count)
            print("completed doc",docid,body_count,file_count)
        elif elem.tag == prefix+"page":
            ## Uncomment this if you need to continue prcessing after a break
            # if docid <= 3780932:
            #     docid += 1
            #     if docid%10000 == 0: print(docid)
            #     elem.clear()
            #     continue
            for w,c in curpage_counts.items():
                temp = words_dict.get(w,0)
                if temp==0:
                    temp = []
                temp.append(c)
                words_dict[w] = temp
            if len(words_dict) >= write_after:
                write_intermediate_index(file_count)
                write_title_index()
                file_count += 1
                page_dict = {}
                words_dict = SortedDict({})
            docid += 1    
            curpage_counts = {}
            elem.clear()
    


if __name__ == "__main__":
    if len(sys.argv)!= 3:
        print("Usage : python3 indexing.py dump.xml ../inverted_indexes_dir_path")
        sys.exit(0)
    output_dir = sys.argv[2]
    with open(output_dir+'/meta_index.txt', 'w') as m:
        pass
    with open(output_dir+'/title_index.txt', 'w') as m:
        pass
    start = time.time()
    with BZ2File(sys.argv[1]) as xml_file:
        context = et.iterparse(xml_file)
        parseXML(context)
    
    write_title_index()
    write_intermediate_index(file_count)
    print("Indexing time:",time.time()-start)