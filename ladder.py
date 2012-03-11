#!/usr/bin/python

import sys

usage_message = 'usage : ladder.py <first word> <second word>'

if len(sys.argv) != 3:
    print usage_message
    sys.exit(1)
elif len(sys.argv[1]) != len(sys.argv[2]):
    print usage_message.join(': both words should have the same length')
    sys.exit(1)

def get_words(length):    # Create a set of the words with the same size
    filename = "words" # English list of words
    words = []
    for x in open(filename):
        if len(x.strip()) == length:
            words.append(x.strip().upper())

    return words

def check_words_exist(words, first_word, second_word):
    return first_word in words and second_word in words

def create_matrice(words):

    i = 0
    j = 0
    matrice = [0] * len(words)
    for i in range(len(words)):
        matrice[i] = [0] * len(words)
        for j in range(len(words)):
            if i != j:
                matrice[i][j] = float("inf")

    return matrice

def dijkstra():

    pass


def main(first_word, second_word):
    words = get_words(len(first_word))
    print len(words)
    #if check_words_exist(words, first_word, second_word):
    #    matrice = create_matrice(words)
    #    dijkstra(matrice)
    #else:
    #    print 'One of the words doesn\'t exist'
    #    sys.exit(1)


main(sys.argv[1], sys.argv[2])
