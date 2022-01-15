import collections
from operator import itemgetter
import re
import sys
import random
import numpy as np

def get_wordle_words(dict_path="/usr/share/dict/words"):
    with open(dict_path, "r") as f:
        words = [line.strip() for line in f]

        # 5 letter words
        words = [word for word in words if len(word) == 5]

        # No proper nouns
        words = [word for word in words if word[0].islower()]

        # No contractions
        words = [word for word in words if not "'" in word]

        # No words with accents
        words = [word for word in words if word.isascii()]

        return words

def get_letter_counts(words):

    # Remove duplicate letters
    dedup_words = [''.join(set(list(word))) for word in words]

    all_letters = ''.join(dedup_words)

    yellow_counter = collections.Counter(all_letters)

    green_counters = [] 

    for i in range(5):
        # All letters in position n
        all_letters = ''.join([word[i] for word in words])

        counter = collections.Counter(all_letters)
        green_counters.append(counter)

    return yellow_counter, green_counters

def get_word_counts(word, yellow_counter, green_counters):
    yellow_count = 0
    green_count = 0

    for i in range(5):
        letter = word[i]
        green_count += green_counters[i][letter]

    for letter in ''.join(set(list(word))):
        yellow_count += yellow_counter[letter]

    return yellow_count, green_count

def filter_words(grey_letters, yellow_letters, green_re, words):
    for letter in yellow_letters:
        words = [word for word in words if letter in word]

    for letter in grey_letters:
        words = [word for word in words if not letter in word]

    words = [word for word in words if re.match(green_re, word)]

    return words

def get_best_word(grey_letters, yellow_letters, re, words, yellow_weight=1.4, green_weight=1):

    words = filter_words(grey_letters, yellow_letters, re, words)

    yellow_counter, green_counters = get_letter_counts(words)

    word_counts = []
    for word in words:
        yellow_count, green_count = get_word_counts(word, yellow_counter, green_counters)
        weighted_sum_count = yellow_weight * yellow_count + green_weight * green_count
        word_counts.append((word, yellow_count, green_count, weighted_sum_count))

    word_counts = sorted(word_counts, key=itemgetter(3), reverse=True)

    best = word_counts[0]

    return best[0]

def gen_hints(guess, solution):
    grey_letters = []
    yellow_letters = [[] for _ in range(5)]
    green_letters = [[] for _ in range(5)]
    
    for i in range(5):
        guess_l = guess[i]
        solution_l = solution[i]

        if solution_l == guess_l:
            green_letters[i] = guess_l
        elif guess_l in solution:
            yellow_letters[i] = [guess_l]
        else:
            grey_letters.append(guess_l)

    return grey_letters, yellow_letters, green_letters

def update_knowlege(hints, knowledge):
    knowledge[0] += hints[0]

    for i in range(5):
        knowledge[1][i] += hints[1][i]
        knowledge[2][i] = hints[2][i]

    return knowledge

def gen_re_from_knowledge(yellow_letters, green_letters):
    re = ""
    for i in range(5):
        if green_letters[i]:
            re += f"[{green_letters[i]}]"
            continue
        elif yellow_letters[i]:
            re += f"[^{''.join(yellow_letters[i])}]"
            continue
        else:
            re += "."
    return re
            
def play(words, solution, yellow_weight, strategy=1):

    grey_letters = []
    yellow_letters = [[] for _ in range(5)]
    green_letters = [[] for _ in range(5)]
    last_guess = ""

    for i in range(20):
        re = gen_re_from_knowledge(yellow_letters, green_letters)

        all_yellow_letters = []
        for letters in yellow_letters:
            all_yellow_letters += letters

        guess = get_best_word(grey_letters, all_yellow_letters, re, words, yellow_weight)
        
        if guess == solution:
            return i + 1

        hints = gen_hints(guess, solution)

        (grey_letters, yellow_letters, green_letters) = update_knowlege(hints, [grey_letters, yellow_letters, green_letters])
        last_guess = guess

    print(f"Could not solve for {solution}. Best guess was {guess}.")

def optimize():
    words = get_wordle_words()

    for i in np.arange(-2, 2, .25):
        yellow_weight = 2 ** i

        iterations = 0
        total_score = 0
        losses = 0

        for solution in words:
            iterations += 1
            score = play(words, solution, yellow_weight)
            total_score += score
            if score > 6:
                losses += 1

        print(f"{yellow_weight}, {total_score/iterations}, {losses/iterations}")

def solve():
    words = get_wordle_words()
    print(get_best_word(sys.argv[1], sys.argv[2], sys.argv[3], words))

if __name__ == "__main__":
    optimize()
    solve()

