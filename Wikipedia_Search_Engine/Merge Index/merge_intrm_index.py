import sys
import tempfile
import os
import heapq
import contextlib
import linecache 
import time
import string
import copy

file_lengths = {}
file_readtill = {}
input_files = {}
output_dir = ""
cur_file_no = 0
total_words = 0
outfile = ""
start = 0

class WordCount(object):
    def __init__(self,val,fno):
        # print(fno,file_readtill[fno],file_lengths[fno],val)
        self.word, self.counts = val.split('|',1)
        self.file_no = fno
        self.word = self.word.strip()
        self.counts = self.counts.strip()
    def __lt__(self,other):
        return self.word < other.word

def create_inverted_index():
    global total_words, start, interval, file_lengths, file_readtill, output_dir, cur_file_no, outfile, input_files
    myheap = []
    for fn in file_lengths:  ## read first line from each intermediate index file
        file_readtill[fn] = 1
        input_files[fn] = open(input_dir+"/index"+str(fn)+".txt")
        firstline = input_files[fn].readline().strip()
        heapq.heappush(myheap,WordCount(firstline,fn))
        print(fn)
    topmin = heapq.heappop(myheap)
    while(True):
        if(len(myheap)==0):
            finished = 0
            for fn in file_lengths:
                if file_readtill[fn] >= file_lengths[fn]:
                    finished += 1
                else:
                    new_line = input_files[fn].readline().strip()
                    heapq.heappush(myheap,WordCount(new_line,fn))
                    file_readtill[fn] += 1
            if finished == len(file_lengths):
                print("finished",cur_file_no)
                outfile.write(topmin.word+"|"+topmin.counts+"\n")
                total_words += 1
                break
        cur_element = copy.deepcopy(topmin)
        if file_readtill[topmin.file_no] < file_lengths[topmin.file_no]:  ## check if lines in that file are over
            new_line = input_files[topmin.file_no].readline().strip()
            heapq.heappush(myheap,WordCount(new_line,topmin.file_no))
            file_readtill[topmin.file_no] += 1
        topmin = heapq.heappop(myheap)
        while(topmin.word == cur_element.word) :
            cur_element.counts += '|'+topmin.counts
            if file_readtill[topmin.file_no] < file_lengths[topmin.file_no]:  ## check if lines in that file are over
                new_line = input_files[topmin.file_no].readline().strip()
                heapq.heappush(myheap,WordCount(new_line,topmin.file_no))
                file_readtill[topmin.file_no] += 1
            if(len(myheap)==0):
                break
            topmin = heapq.heappop(myheap)
        outfile.write(cur_element.word+"|"+cur_element.counts+"\n")
        total_words += 1
        # print(cur_file_no, cur_element.file_no, cur_element.word, total_words)
    for f in input_files:
        input_files[f].close()
    with open(output_dir+"/meta_intrmindex.txt", 'a') as mf:
        mf.write(str(cur_file_no)+" "+str(total_words)+"\n")
        
    
if __name__ == "__main__":
    ## usage: !python merge_intrm_index.py right_etbig_inverted_indexes/ right_etbig_inverted_indexes/ 0 1724 4
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    st = int(sys.argv[3])
    end = int(sys.argv[4])
    interval = int(sys.argv[5])
    with open(output_dir+"/meta_intrmindex.txt", 'w') as mf:
        pass
    cur_file_no = st//interval
    for x in range(st,end,interval):
        print("************ START ",x,"***************")
        total_words = 0
        start = x
        file_lengths = {}
        file_readtill = {}
        outfile = open(output_dir+"/intrmindex_"+str(cur_file_no)+".txt",'w+')
        for k in range(x,x+interval):
            file_lengths[k] = int(linecache.getline(input_dir+"/meta_index.txt",k+1).strip().split()[1])
        print(file_lengths)
        create_inverted_index()
        outfile.close()
        print(cur_file_no,total_words)
        cur_file_no += 1
        
    