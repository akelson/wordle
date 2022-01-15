import collections
from operator import itemgetter
import re
import sys
import random
import numpy as np
import argparse

OPTIM_YELLOW_WEIGHT = 1.4

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

def get_best_word(grey_letters, yellow_letters, re, words, yellow_weight, green_weight=1):

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
            
def play(words, solution, yellow_weight=OPTIM_YELLOW_WEIGHT, strategy=1):

    grey_letters = []
    yellow_letters = [[] for _ in range(5)]
    green_letters = [[] for _ in range(5)]
    guesses = []

    for i in range(20):
        re = gen_re_from_knowledge(yellow_letters, green_letters)

        all_yellow_letters = []
        for letters in yellow_letters:
            all_yellow_letters += letters

        guess = get_best_word(grey_letters, all_yellow_letters, re, words, yellow_weight)
        guesses.append(guess)
        
        if guess == solution:
            return guesses

        hints = gen_hints(guess, solution)

        (grey_letters, yellow_letters, green_letters) = update_knowlege(hints, [grey_letters, yellow_letters, green_letters])

def optimize():
    words = get_wordle_words()

    for i in np.arange(-2, 2, .25):
        yellow_weight = 2 ** i

        iterations = 0
        total_score = 0
        losses = 0

        for solution in words:
            iterations += 1
            guesses = play(words, solution, yellow_weight)
            score = len(guesses)
            total_score += score
            if score > 6:
                losses += 1

        print(f"{yellow_weight}, {total_score/iterations}, {losses/iterations}")

def solve(grey_letters, yellow_letters, regex):
    words = get_wordle_words()
    print(get_best_word(grey_letters, yellow_letters, regex, words, OPTIM_YELLOW_WEIGHT))

def solve_cmd(args):
    solve(args.grey, args.yellow, args.regex)

def play_cmd(args):
    words = get_wordle_words()

    try:
        print("\n".join(play(words, args.solution)))
    except:
        print(f"Could not solve for '{args.solution}'.", file=sys.stderr)

def optimize_cmd(args):
    optimize()

def solution_checker(solution):
    if len(solution) != 5:
        raise argparse.ArgumentTypeError("Solution must have 5 letters!")
    return solution

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="command", dest="command", required=True)

    parser_solve = subparsers.add_parser("solve", description="solve a puzzle")
    parser_solve.add_argument("--grey", help="grey letters")
    parser_solve.add_argument("--yellow", help="yellow letters")
    parser_solve.add_argument("--regex", help="regular expression")
    parser_solve.set_defaults(grey="", yellow="", regex=".....", func=solve_cmd)

    parser_play = subparsers.add_parser("play", description="play for a given solution")
    parser_play.add_argument("solution", type=solution_checker)
    parser_play.set_defaults(func=play_cmd)

    parser_optim = subparsers.add_parser("optimize", description="optimize weights")
    parser_optim.set_defaults(func=optimize_cmd)

    args = parser.parse_args()
    args.func(args)
