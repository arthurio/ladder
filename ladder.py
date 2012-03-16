#!/usr/bin/python

#@author: Arthur Rio
#@Copyright: 2012
#@Description: This algorithm use threads to search in cross directions 
#              the ladder path between two words. The search is based on
#              a graph exploration.

import random, thread
from threading import Thread, Lock

# Create a set of the words with the same size
def get_words(length, input_path):
    filename = input_path 
    words = []
    for x in open(filename):
        if len(x.strip()) == length:
            words.append(x.strip().upper())

    return words

# Check if the words are in the input file
def check_words_exist(words, first_word, second_word):
    return first_word in words and second_word in words

# Main class to find the ladder path
class Searcher(Thread):

    # Number of threads to use
    NUMBER_OF_SEARCHERS = 5

    # Type of Searcher
    TYPE_FIRST_SECOND = 0 # Start from the first word
    TYPE_SECOND_FIRST = 1 # Start from the last word

    # Counter of the number of threads terminated because of exception
    INTERRUPT = 0

    # Locks shared between threads
    lock_found = Lock()
    lock_matrix = Lock()
    lock_list = Lock()
    lock_error = Lock()

    # Class variables
    found = False # Tells that a path has been found
    list_first = {} # Dict of (found word, thread) for the first kind of threads
    list_second = {} # Dict of (found word, thread) for the second kind of threads
    matrix = {} # matrix of possible next words for a given one
                # building it as the search progress avoid to go
                # through all the words of the input file


    # Constructor
    def __init__(self, start_word, end_word, type_thread):
        self.start_word = start_word
        self.end_word = end_word
        self.path = []
        self.type_thread = type_thread
        super(Searcher, self).__init__(target=self.search)
        self.start()

    # Main function
    def search(self):
        while True:
            # Stop the thread if a path has been found
            with Searcher.lock_found:
                if Searcher.found:
                    break

            # Check if the last word of the current path is in the list of the other direction search
            with Searcher.lock_list:
                # Append the current word to the end of the path
                self.path.append(self.start_word)
                # Look for the type of thread
                if self.type_thread == Searcher.TYPE_FIRST_SECOND:
                    if self.start_word in Searcher.list_second:
                        # find the matching word
                        second_path = Searcher.list_second[self.start_word].get_path()
                        word_index = second_path.index(self.start_word)
                        # take the path until the word behind the matching one
                        second_path = second_path[0:word_index]
                        second_path.reverse()
                        # build the path from the two lists
                        self.set_found(self.path + second_path)
                        break
                    else:
                        # if not found and not already in the dict found words, append the word to it
                        if self.start_word not in Searcher.list_first:
                            Searcher.list_first[self.start_word] = self
                else:
                    if self.start_word in Searcher.list_first:
                        # find the matching word
                        first_path = Searcher.list_first[self.start_word].get_path()
                        word_index = first_path.index(self.start_word)
                        # take the path until the word behind the matching one
                        first_path = first_path[0:word_index]
                        self.path.reverse()
                        # build the path from the two lists
                        self.set_found(first_path + self.path)
                        break
                    else:
                        # if not found and not already in the dict found words, append the word to it
                        if self.start_word not in Searcher.list_second:
                            Searcher.list_second[self.start_word] = self

            # If the current word and the end word has one letter that differs, the path is found!
            if self.hamming_distance(self.start_word, self.end_word) == 1:
                # append the end word to the path
                self.path.append(self.end_word)
                # stop the search
                self.set_found(self.path)
                break
            else:
                # Build the matrix of [words/possible next words]
                with Searcher.lock_matrix:
                    if not self.start_word in Searcher.matrix:
                        Searcher.matrix[self.start_word] = []
                        for w in Searcher.words:
                            if self.hamming_distance(w, self.start_word) == 1:
                                Searcher.matrix[self.start_word].append(w)

                try:
                    with Searcher.lock_list:
                        # Take a word that has not been explored yet
                        if self.type_thread == Searcher.TYPE_FIRST_SECOND:
                            other_list = Searcher.list_first
                            list_of_choices = list(set(Searcher.matrix[self.start_word]) - set(other_list.keys()))
                        else:
                            other_list = Searcher.list_second
                            list_of_choices = list(set(Searcher.matrix[self.start_word]) - set(other_list.keys()))

                    # if all the words has already been searched go back to the previous one
                    if (len(list_of_choices) == 0):
                        # if more than one remaining
                        if (len(self.path) > 1):
                            # restart from the previous node
                            self.path.pop()
                            self.start_word = self.path.pop()
                        else:
                            # End the thread if no more exploration can be done
                            # All the words of its path has been explored and
                            # either taken care of by another thread or concluded
                            # to a dead end
                            raise IndexError
                    else:
                        # take two random words from the list of choices
                        w1 = random.choice(list_of_choices)
                        w2 = random.choice(list_of_choices)
                        # keep the best one
                        self.start_word = self.best_word(w1, w2)
                except IndexError:
                    # The thread is in a dead end and cannot try another path
                    with self.lock_error:
                        # if all the threads have been stopped
                        if Searcher.INTERRUPT == Searcher.NUMBER_OF_SEARCHERS * 2:
                            print 'Cannot find a path between those two words'
                            thread.exit()
                        # Set this thread to stopped
                        else:
                            print 'One thread dead'
                            print self.path
                            Searcher.INTERRUPT += 1
                            break


    # Return the word that match the most with the end_word
    def best_word(self, w1, w2):
        if self.hamming_distance(w1, self.end_word) < self.hamming_distance(w2, self.end_word):
            return w1
        else:
            return w2

    # Return the path of the current thread
    def get_path(self):
        return self.path

    # Set the class variable found to True to stop the other threads and print the result
    def set_found(self, path):
        with Searcher.lock_found:
            if not Searcher.found:
                print '%s %s %s' % (path[0], path[len(path) - 1], len(path))
                print path
                Searcher.found = True

    # Compute distance between the two words
    def hamming_distance(self, s1, s2):
        return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))

# Main program
def main(first_word, second_word):

    # Define number of threads to use
    searcher_count = Searcher.NUMBER_OF_SEARCHERS
    # keep the list of threads
    threads = []

    # Check if the words exist in the input file
    if check_words_exist(Searcher.words, first_word, second_word):
        for i in range(searcher_count):
            # Execute one thread in each direction to cross the results
            threads.append(Searcher(first_word, second_word, Searcher.TYPE_FIRST_SECOND))
            threads.append(Searcher(second_word, first_word, Searcher.TYPE_SECOND_FIRST))

        # Wait until all the threads are finished
        for t in threads:
            t.join()

    else:
        print 'At least one of the words doesn\'t exist'

if __name__ == '__main__':

    while True:

        # Init Searcher
        Searcher.found = False
        Searcher.list_first = {}
        Searcher.list_second = {}
        Searcher.matrix = {}

        # Use inputs to load the program
        input_words = raw_input('word file path (press enter to use default): ')
        first_word = raw_input('first word: ').upper().strip()
        second_word = raw_input('second word: ').upper().strip()

        if input_words == '' :
            # The default words file is the Mac OSX English list of words from /usr/share/dict/words
            input_words = 'words'

        # Check if the two words have the same length
        if len(first_word) != len(second_word):
            print 'The two words must have the same length'
            break

        try:
            # Initialize the list of words to search in
            Searcher.words = get_words(len(first_word), input_words)
            # Run the main program
            main(first_word, second_word)
        except IOError:
            print 'The input file has not been found, please check your path'
            continue
