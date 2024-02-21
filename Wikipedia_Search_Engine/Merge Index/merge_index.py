import sys
import tempfile
import os
import heapq
import contextlib
import linecache 
import time
import string
import copy

file_lengths = []
output_files = []
input_files = []
offset_files = []
offsets = []
file_readtill = []
output_lengths = []
output_dir = ""
input_dir = ""
total_words = 0

class WordCount(object):
    def __init__(self,val,fno):
        self.word, self.counts = val.split('|',1)
        self.file_no = fno
        self.word = self.word.strip()
        self.counts = self.counts.strip()
    def __lt__(self,other):
        return self.word < other.word

def create_inverted_index():
    global total_words, file_lengths, output_files, input_files, file_readtill, output_lengths, output_dir, input_dir, offset_files, offsets
    myheap = []
    for fnum in range(len(file_lengths)):  ## read first line from each intermediate index file
        file_readtill.append(1)
        infile = open(input_dir+"/intrmindex_"+str(fnum)+".txt")
        input_files.append(infile)
        firstline = input_files[fnum].readline().strip()
        heapq.heappush(myheap,WordCount(firstline,fnum))
        print(fnum)
    for a in ['0']+list(string.ascii_lowercase):  ## create final index files
        outfile = open(output_dir+"/invindex_"+a+".txt",'w+')
        output_files.append(outfile)
        output_lengths.append(0)
        offfile = open(output_dir+"/invoffset_"+a+".txt",'w+')
        offset_files.append(offfile)
        offsets.append(0)
    topmin = heapq.heappop(myheap)
    while(True):
        if(len(myheap)==0):
            finished = 0
            for fnum in range(len(file_lengths)):
                if file_readtill[fnum] >= file_lengths[fnum]:
                    finished += 1
                else:
                    new_line = input_files[fnum].readline().strip()
                    heapq.heappush(myheap,WordCount(new_line,fnum))
                    file_readtill[fnum] += 1
            if finished == len(file_lengths):
                char1 = topmin.word[0]
                line = topmin.word+"|"+topmin.counts+"\n"
                if char1.isnumeric():
                    idx = 0
                else:
                    idx = ord(char1)-ord('a')+1
                output_files[idx].write(line)
                offset_files[idx].write(str(offsets[idx])+"\n")
                output_lengths[idx] += 1
                offsets[idx] += len(line)
                total_words += 1
                break
        cur_element = copy.deepcopy(topmin)
        # print(cur_element.file_no, cur_element.word, len(myheap))
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
        char1 = cur_element.word[0]
        line = cur_element.word+"|"+cur_element.counts+"\n"
        if char1.isnumeric():
            idx = 0
        else:
            idx = ord(char1)-ord('a')+1
        output_files[idx].write(line)
        offset_files[idx].write(str(offsets[idx])+"\n")
        output_lengths[idx] += 1
        offsets[idx] += len(line)
        total_words += 1
        print(cur_element.file_no, cur_element.word, total_words)
    for f in input_files:
        f.close()
    for f in output_files:
        f.close()
    for f in offset_files:
        f.close()
    with open(output_dir+"/meta_invindex.txt") as mf:
        for ol in output_lengths:
            mf.write(str(ol)+"\n")
        
    
if __name__ == "__main__":
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    with open(input_dir+"/meta_intrmindex.txt") as mf:
        for line in mf:
            file_lengths.append(int(line.strip().split()[1]))
    create_inverted_index()
    print(total_words)
    print(file_lengths)
    print(file_readtill)
    