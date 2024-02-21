import re
import nltk
import string
from Stemmer import Stemmer
from nltk.corpus import stopwords as nltk_stopwords
import time
import linecache
import json
import sys
import math
import operator
import heapq

stopwords = list(nltk_stopwords.words('english'))
stemmer = Stemmer('english')
total_docs = 14764785 #21350000
min_words_in_doc = 20
field_weight = 5
title_weight = 10
doc_length_dict = []
index_length_dict = []
min_word_len = 3
offsets = []
index_files = []

def open_files():
    global index_length_dict, doc_length_dict, offsets, index_files
    ## read title_index and store docid with num of words
    with open(vocab_dir+'/title_index.txt') as f1:
        for line in f1:
            docid, title, num_words = line.strip().split('|')
            doc_length_dict.append(int(num_words.strip()))
    for a in ['0']+list(string.ascii_lowercase):
        cur_offs = []
        with open(vocab_dir+'/invoffset_'+a+'.txt') as f:
            for line in f:
                cur_offs.append(int(line.strip()))
        offsets.append(cur_offs)
        idx_file = open(vocab_dir+'/invindex_'+a+'.txt') 
        index_files.append(idx_file)
    ## read meta_invindex to get how many lines each file has
    for offs in offsets:
        index_length_dict.append(len(offs))
    # print(len(doc_length_dict),len(index_length_dict),len(offsets))

def close_files():
    global index_files
    for idf in index_files:
        idf.close()
        
def binary_search(l, r, w, fpath, idx):
    while r >= l:
        mid = (l + r) // 2
        index_files[idx].seek(offsets[idx][mid])
        cur_line = index_files[idx].readline()
        cur_word = cur_line.split('|',1)[0]
        if  cur_word == w:
            return cur_line
        elif cur_word > w:
            r = mid-1
        else:
            l = mid+1
    return -1

def search_word(orgword,section):
    global default_res, total_docs, min_words_in_doc, field_weight, doc_length_dict, doc_score_dict, min_word_len
    if len(orgword) < min_word_len:
        return 
    word = orgword
    if word in stopwords:
        return
    word = stemmer.stemWord(word)
    char1 = word[0]
    if char1.isnumeric():
        idx = 0
        char1 = '0'
    else:
        idx = ord(char1)-ord('a')+1
    cur_line = binary_search(0,index_length_dict[idx],word,vocab_dir+"/invindex_"+char1+".txt",idx)
    if cur_line == -1:
        return
    cur_list = cur_line.split('|')
    term_idf = math.log(total_docs / len(cur_list))
    if not cur_list[0] == word:
        return
    term_all_score = 0
    for i in range(1,len(cur_list)):
        cur_id, cur_cnts = cur_list[i].split(';',1) 
        cur_id = int(cur_id.strip())
        if doc_length_dict[cur_id] < min_words_in_doc:
            continue
        cur_cnts = cur_cnts.split(';')
        cur_score = 0  ## current document's score
        for cnt in cur_cnts:
            if 't' in cnt:
                c = int(cnt.split('t')[1])
                cur_score += title_weight * c
                if 't' in section:
                    cur_score += field_weight * c
            if 'b' in cnt:
                c = int(cnt.split('b')[1])
                cur_score += c
                if 'b' in section:
                    cur_score += field_weight * c
            if 'i' in cnt:
                c = int(cnt.split('i')[1])
                cur_score += c
                if 'i' in section:
                    cur_score += field_weight * c
            if 'c' in cnt:
                c = int(cnt.split('c')[1])
                cur_score += c
                if 'c' in section:
                    cur_score += field_weight * c
            if 'l' in cnt:
                c = int(cnt.split('l')[1])
                cur_score += c
                if 'l' in section:
                    cur_score += field_weight * c
        term_freq = math.log(1+cur_score)
        cur_score = term_freq * term_idf
        if cur_id not in doc_score_dict:
            doc_score_dict[cur_id] = cur_score
        else:
            doc_score_dict[cur_id] += cur_score
        term_all_score += cur_score
    # print("Score for word ",orgword,":",term_all_score) 


def search_query(query):
    global doc_score_dict, min_word_len
    query = query.strip().lower()
    qwlist = [e.strip()+':' for i,e in enumerate(query.strip().split(':')) if e]
    qwlist[-1] = qwlist[-1][:-1]
    query_dict = {}
    field = '0'
    for qry in qwlist: 
        for w in qry.split(' '):
            if not w:
                continue
            if ':' in w:
                field = w.split(':')[0].strip()
                if field not in ['t', 'b', 'c', 'i', 'l']:
                    field = 'b'
                cw = ''
            else:
                cw = w.strip()
            if cw:
                # search_word(cw,field)
                if cw not in query_dict:
                    query_dict[cw] = field
                else:
                    query_dict[cw] += field
                cw = ""
    for qw, qf in query_dict.items():
        # print(qw,qf)
        search_word(qw,qf)
        

def print_results(topk=12):
    global doc_score_dict, vocab_dir
    print("\n******** Search Results ********")
    top_pages = heapq.nlargest(topk, doc_score_dict, key=doc_score_dict.get)
    i = 0
    for docid in top_pages:
        cur_line = linecache.getline(vocab_dir+"/title_index.txt",docid+1).strip()
        cur_id, cur_title, cur_words = cur_line.split('|')
        cur_id = int(cur_id)
        if cur_id != docid:
            err = math.abs(cur_id - docid) + 1
            cur_line = binary_search(cur_id-err, cur_id+err, str(doc_id), vocab_dir+"/title_index.txt")
            cur_id, cur_title, cur_words = cur_line.split('|')
        print("rank:",i,"\tpage_id:",cur_id,"\ttotal_words_in_page:",cur_words,"\ttitle:",cur_title)
        if i==10:
            return
        i += 1
        

if __name__ == "__main__":
    global vocab_dir, doc_score_dict
    vocab_dir = sys.argv[1]  #"right_etbig_inverted_indexes/inv_indexes/"
    testqfile = sys.argv[2]
    open_files()
    test_qlist = []
    print("Opening files ...")
    with open(testqfile) as qfile:
        for line in qfile:
            test_qlist.append(line.strip())
    for in_query in test_qlist:
        print("\n########################################################################")
        print(in_query)
        doc_score_dict = {}
        start = time.time()
        search_query(in_query.strip())
        print_results(12)
        print("\nSearch time:",time.time()-start)
    close_files()
    