#!/usr/bin/python

import sys, pickle, random, math
from threading import Thread, Lock

usage_message = 'usage : ladder.py <first word> <second word>'

def progress(width, percent):
    marks = math.floor(width * (percent / 100.0))
    spaces = math.floor(width - marks)
     
    loader = '[' + ('=' * int(marks)) + (' ' * int(spaces)) + ']'
       
    sys.stdout.write("%s %d%%\r" % (loader, percent))
    if percent >= 100:
        sys.stdout.write("\n")
    sys.stdout.flush()


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

    for i, w1 in enumerate(words):
        progress(100, (float(i) / len(words)) * 100)
        if w1 not in matrix:
            matrix[w1] = []
        for j in range(i + 1, len(words)):
            if hamming_distance(w1, words[j]) == 1:
                matrix[w1].append(words[j])
                if words[j] not in matrix:
                    matrix[words[j]] = []
                matrix[words[j]].append(w1)

    print '100%'
    return matrix


def dump_matrix(size):
    pickle.dump(create_matrix(get_words(size)), open('matrix_%s.pkl' % size, 'wb'))


class Searcher(Thread):

    lock_found = Lock()
    lock_matrix = Lock()
    found = False
    matrix = {}

    def __init__(self, start_word, end_word):
        self.start_word = start_word
        self.end_word = end_word
        self.path = []
        super(Searcher, self).__init__(target=self.search)
        self.start()

    def search(self):
        while True:
            with Searcher.lock_found:
                if Searcher.found:
                    break

            self.path.append(self.start_word)
            if self.start_word in Searcher.matrix and self.end_word in Searcher.matrix[self.start_word]:
                self.path.append(self.end_word)
                with Searcher.lock_found:
                    Searcher.found = True
                    print self.path
                    break
            else:
                with Searcher.lock_matrix:
                    if not self.start_word in Searcher.matrix:
                        Searcher.matrix[self.start_word] = []
                        for w in Searcher.words:
                            if hamming_distance(w, self.start_word) == 1:
                                Searcher.matrix[self.start_word].append(w)

                w1 = random.choice(Searcher.matrix[self.start_word])
                w2 = random.choice(Searcher.matrix[self.start_word])
                self.start_word = self.best_word(w1, w2)
                    
    def best_word(self, w1, w2):
        if hamming_distance(w1, self.end_word) < hamming_distance(w2, self.end_word):
            return w1
        else:
            return w2

    def hamming_distance(s1, s2):
        return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))

        
def main(first_word, second_word):

    searcher_count = 5
    threads = []

    if check_words_exist(Searcher.words, first_word, second_word):
        for i in range(searcher_count):
            threads.append(Searcher(first_word, second_word))
            threads.append(Searcher(second_word, first_word))

        for t in threads:
            t.join()
    else:
        print 'One of the words doesn\'t exist'
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print usage_message
        sys.exit(1)
    elif len(sys.argv[1]) != len(sys.argv[2]):
        print usage_message.join(': both words should have the same length')
        sys.exit(1)

    Searcher.words = get_words(len(sys.argv[1]))
    
    import profile

    profile.run('main("%s", "%s")' % (sys.argv[1], sys.argv[2]))
