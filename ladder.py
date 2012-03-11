#!/usr/bin/python

import sys, time, pickle, random
from threading import Thread

usage_message = 'usage : ladder.py <first word> <second word>'

def get_words(length):    # Create a set of the words with the same size
    filename = "words" # English list of words
    words = []
    for x in open(filename):
        if len(x.strip()) == length:
            words.append(x.strip().upper())

    return words

def check_words_exist(words, first_word, second_word):
    return first_word in words and second_word in words


def hamming_distance(s1, s2):
    return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))
    
def create_matrix(words):

    matrix = {}
    for w1 in words:
        matrix[w1] = []
        for w2 in words:
            if hamming_distance(w1, w2) == 1:
                matrix[w1].append(w2)

    return matrix

class Searcher(Thread):
    def __init__(self, start_word, end_word, words):
        self.words = words
        self.start_word = start_word
        self.end_word = end_word
        self.path = []
        super(Searcher, self).__init__(target=self.search)
        self.start()

    def search(self):
        print "search"
        while True:
            self.path.append(self.start_word)
            if self.end_word in words[self.start_word]:
                self.path.append(self.end_word)
                print "TROUVE"
                print self.path
                sys.exit(1)
            else:
                next_word = random.choice(words[self.start_word])
                self.start_word = next_word

    def is_better(self):
        return True
        
words = pickle.load(open('matrix.pkl','r'))
#words = get_words(len(first_word))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print usage_message
        sys.exit(1)
    elif len(sys.argv[1]) != len(sys.argv[2]):
        print usage_message.join(': both words should have the same length')
        sys.exit(1)

    searcher_count = 5
    first_word = sys.argv[1]
    second_word = sys.argv[2]
    threads = []
    
    if check_words_exist(words, first_word, second_word):
        for i in range(searcher_count):
            threads.append(Searcher(first_word, second_word, words))
            threads.append(Searcher(second_word, first_word, words))

        for t in threads:
            t.join()
    else:
        print 'One of the words doesn\'t exist'
        sys.exit(1)
