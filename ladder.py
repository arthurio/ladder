#!/usr/bin/python

import sys, pickle, random, math, thread
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
        progress(100, (float(i+1) / len(words)) * 100)
        if w1 not in matrix:
            matrix[w1] = []
        for j in range(i + 1, len(words)):
            if hamming_distance(w1, words[j]) == 1:
                matrix[w1].append(words[j])
                if words[j] not in matrix:
                    matrix[words[j]] = []
                matrix[words[j]].append(w1)

    return matrix


def dump_matrix(size):
    pickle.dump(create_matrix(get_words(size)), open('matrix_%s.pkl' % size, 'wb'))


class Searcher(Thread):

    NUMBER_OF_THREADS = 5

    THREAD_FIRST = 0
    THREAD_SECOND = 1

    INTERRUPT = 0

    lock_found = Lock()
    lock_matrix = Lock()
    lock_list = Lock()
    lock_error = Lock()
    found = False
    list_first = {}
    list_second = {}
    matrix = {}


    def __init__(self, start_word, end_word, type_thread):
        self.start_word = start_word
        self.end_word = end_word
        self.path = []
        self.type_thread = type_thread
        super(Searcher, self).__init__(target=self.search)
        self.start()

    def search(self):
        while True:
            if Searcher.INTERRUPT == Searcher.NUMBER_OF_THREADS * 2:
                break

            with Searcher.lock_found:
                if Searcher.found:
                    break

            with Searcher.lock_list:
                self.path.append(self.start_word)
                if self.type_thread == Searcher.THREAD_FIRST:
                    if self.start_word in Searcher.list_second:
                        # find the matching word
                        second_path = Searcher.list_second[self.start_word].get_path()

                        # TODO here we display the two paths before modification to see what is going on, should use the print in set_found instead
                        print 'First thread'
                        print self.path, second_path

                        word_index = second_path.index(self.start_word)
                        # take the path until the word behind the matching one
                        second_path = second_path[0:word_index]
                        second_path.reverse()
                        # find the matching word
                        self.set_found(self.path + second_path)
                        break
                    else:
                        if self.start_word not in Searcher.list_first:
                            Searcher.list_first[self.start_word] = self
                else:
                    if self.start_word in Searcher.list_first:
                        # find the matching word
                        first_path = Searcher.list_first[self.start_word].get_path()

                        #TODO here we display the two paths before modification to see what is going on, should use the print in set_found instead
                        print 'Second thread'
                        print first_path, self.path

                        word_index = first_path.index(self.start_word)
                        # take the path until the word behind the matching one
                        first_path = first_path[0:word_index]

                        self.path.reverse()

                        self.set_found(first_path + self.path)
                        break
                    else:
                        if self.start_word not in Searcher.list_second:
                            Searcher.list_second[self.start_word] = self

            if hamming_distance(self.start_word, self.start_word) == 1:
                self.path.append(self.end_word)
                print 'Self found'
                self.set_found(self.path)
                break
            else:
                with Searcher.lock_matrix:
                    if not self.start_word in Searcher.matrix:
                        Searcher.matrix[self.start_word] = []
                        for w in Searcher.words:
                            if hamming_distance(w, self.start_word) == 1:
                                Searcher.matrix[self.start_word].append(w)

                try:
                    with Searcher.lock_list:
                        if self.type_thread == Searcher.THREAD_FIRST:
                            other_list_keys = Searcher.list_first.keys()
                            list_of_choices = list(set(Searcher.matrix[self.start_word]) - set(other_list_keys))
                        else:
                            other_list_keys = Searcher.list_second.keys()
                            list_of_choices = list(set(Searcher.matrix[self.start_word]) - set(other_list_keys))

                    # if all the words has already been searched go back to the previous one
                    if (len(list_of_choices) == 0):
                        self.path.pop(len(self.path) - 1)
                        # if no previous one, start with the last found to continue the search
                        if (len(self.path) == 0):
                            self.start_word = other_list_keys[len(other_list_keys) - 1]
                        else:
                            self.start_word = self.path[len(self.path) - 1]

                    else:
                        w1 = random.choice(list_of_choices)
                        w2 = random.choice(list_of_choices)
                        self.start_word = self.best_word(w1, w2)
                except IndexError as e:
                    print e
                    with self.lock_error:
                        print Searcher.INTERRUPT, Searcher.NUMBER_OF_THREADS * 2
                        if Searcher.INTERRUPT == Searcher.NUMBER_OF_THREADS * 2:
                            print 'Cannot find a path between those two words'
                            thread.exit()
                        else:
                            Searcher.INTERRUPT += 1
                    break


                    
    def best_word(self, w1, w2):
        if hamming_distance(w1, self.end_word) < hamming_distance(w2, self.end_word):
            return w1
        else:
            return w2

    def get_path(self):
        return self.path

    def set_found(self, path):
        Searcher.found = True
        print path

    def hamming_distance(s1, s2):
        return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))

        
def main(first_word, second_word):

    searcher_count = Searcher.NUMBER_OF_THREADS
    threads = []

    if check_words_exist(Searcher.words, first_word, second_word):
        for i in range(searcher_count):
            threads.append(Searcher(first_word, second_word, Searcher.THREAD_FIRST))
            threads.append(Searcher(second_word, first_word, Searcher.THREAD_SECOND))

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
