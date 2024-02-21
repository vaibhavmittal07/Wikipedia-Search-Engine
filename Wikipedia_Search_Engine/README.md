# IRE Mini Project - Wikipedia Search Engine

### 1. Indexer  
#### indexer.py : To parse the XML dump and create (intermediate) inverted index  
* Used ElementTree XML parser on the zipped XML dump directly using BZ2 library without loading the entire dump into memory. 
* Segregated sections in text such as : title(t), categories\(c\), external links(l), infobox(i), body(b) (remaining text). 
* Steps used for processing text are :  1) Casefolding (everything to lowercase), 2) Tokenization (removed symbols and separated words), 3) Filtered words (removed stopwords, removed words containing digits if not in title), 4) Stemming (converted words into root words using PyStemmer). Option to use Lemmatizer is included. 
* Created posting lists of words in the format : word|pageid;t1;b5;i2|pageid;b2;c1|pageid;l2;b3 where pageid is the self-generated page id and numbers alongside letters are the counts of the word in respective sections of that page. Used SortedDict to sort (asc) the posting lists wrt words.
* Dumped the block of sorted posting lists into intermediate index files along with metadata after the word-limit is crossed.  

### 2. Merge Index
#### merge_index.py : To merge intermediate index files into final sorted inverted index  
* Implemented k-way external merge sort on the intermediate sorted index files.
* Created 27 final inverted index files, 26 for each alphabet (all posting lists of words starting with a will be in a.txt and likewise for others) and 1 for all numerical words (taken only from titles).
* Created 27 word offset files to store the offset of each word (how many characters to move ahead from the file's start to reach that word) for the respective inverted index files.  

### 3. Search
#### search.py : To obtain top N wiki-pages for the search queries  
* Removed stopwords from query, used stemmer, segregated query words, grouped query fields of unique words.
* Applied binary search on inverted index files to get the query word and its posting list with the help of offsets using indexfile.seek(offset) in Logarithmic time.
* Used Tf-Idf metric for calculating page scores for each word, gave higher weightage to the titles (always) and query fields (if asked) and added scores for found pages (union) into a global dictionary.
* Fetched top N pages with highest scores using max heap.
* Included support for plain as well as multi-field queries.
