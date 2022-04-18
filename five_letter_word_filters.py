"""Filters to narrow down a set of 5-letter-words"""
import argparse
import copy
import itertools
import sys
import re

from datetime import datetime
from pprint import pprint
from typing import Iterable, List, OrderedDict

import five_letter_word_set
from wordle_game import WordleGuesser


def parse_filter_spec(spec: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--starts", help="word starts with one or more provided letters")
    parser.add_argument("-e", "--ends", help="word ends with one or more provided letters")
    parser.add_argument(
        "-c",
        "--contains",
        help="the middle 3 letters have the 1, 2, or 3 provided letters. Use a "
        "dot for a wildcard, like a.b, .ab, or ab. ",
    )
    parser.add_argument("-n", "--not-contains", help="one or more letters that each appear no where in the word")
    parser.add_argument(
        "-a",
        "--all",
        help="all of the provided letters appear one or more times in the word, "
        "not necessarily in the order provided",
    )
    parser.add_argument(
        "-p",
        "--positions",
        nargs="+",
        help="specify which letter a position IS, or IS not. Repeat "
        "this arg as much as 10 times (5 for IS, 5 for IS NOT). "
        "For non-matches, preceed one or more letters with a !. "
        "Examples: -p 1a -p 2x -p 5!est",
    )
    parser.add_argument(
        "--no-repeats",
        action="store_true",
        help="filter out words that repeat a letter more than once",
    )
    parser.add_argument(
        "--no-plurals",
        action="store_true",
        help="filter out words that end in 'S' and look to be a plural",
    )
    parser.add_argument(
        "--no-past-tense",
        action="store_true",
        help="filter out words that seem to be in past-tense",
    )
    parser.add_argument(
        "-x",
        "--expanded-word-list",
        action="store_true",
        help="use all US 5-letter words if provided, otherwise use the pruned down curated words list",
    )
    parser.add_argument(
        "-X",
        "--exclude-words",
        nargs="+",
        help="space-separated list of words to exclude",
    )
    parser.add_argument(
        "-R",
        "--positional-ranking-matrix",
        nargs="?",  # allow 0 or 1 value (counted as space-delimited)
        const="*",  # default value when arg provided with no value
        help="Print out a matrix of each of the given letters (leave empty or use * to print all candidate letters), and their occurrence in each position, "
        "given all the other filters applied",
    )
    parser.add_argument(
        "-g",
        "--pick-next-guess",
        nargs="?",  # allow 0 or 1 value (counted as space-delimited)
        const="10",  # default value when arg provided with no value
        type=int,
        help="Provides the best guess to use which will weed out the most answers. Uses the entire expanded words list, unfiltered, as guess candidates and simulate use of each guess against each of the answer options from the provided filter. Rank guesses (10 ranked by default if a number not provided) by their score, where a lower score means least answer options per guess on avg (best score of 1.00). See also --show-next-guess-results"
    )
    parser.add_argument(
        "--G",
        nargs="?",  # allow 0 or 1 value (counted as space-delimited)
        const="10",  # default value when arg provided with no value
        type=int,
        help="Same as -g, but limits guess candidates to the filtered down words."
    )
    parser.add_argument(
        "--Gx",
        nargs="?",  # allow 0 or 1 value (counted as space-delimited)
        const="10",  # default value when arg provided with no value
        type=int,
        help="Same as --G, but rebuilds guess list to be those from the expanded words list matching the filter"
    )
    parser.add_argument(
        "--show-next-guess-results",
        action="store_true",
        default=False,
        help="When using -g, --G, or --Gx to pick the highest ranked next guess, also add this arg to print out the guess results for each answer+guess combo",
    )
    return parser.parse_args(spec.split())


def filter_words(word_set: Iterable, filter_args):
    filtered_words = iter(word_set)
    if filter_args.starts:
        filtered_words = filter(lambda w: w.startswith(filter_args.starts), filtered_words)
    if filter_args.ends:
        filtered_words = filter(lambda w: w.endswith(filter_args.ends), filtered_words)
    if filter_args.contains:
        if "." in filter_args.contains:
            filtered_words = filter(lambda w: bool(re.match(filter_args.contains, w[1:-1])), filtered_words)
        else:
            filtered_words = filter(lambda w: filter_args.contains in w[1:-1], filtered_words)
    if filter_args.not_contains:
        filtered_words = filter(lambda w: all([l not in w for l in filter_args.not_contains]), filtered_words)
    if filter_args.all:
        if len(set(filter_args.all)) > 5:
            # If more than 5 letters are provided, the word must contain all letters of some 5-letter subset
            filtered_words = filter(lambda w: sum([w.count(l) for l in set(filter_args.all)]) >= 5, filtered_words)
        else:
            filtered_words = filter(lambda w: all([l in w for l in filter_args.all]), filtered_words)
    if filter_args.positions:
        exact_matches = {int(pl[0]) - 1: pl[1] for pl in filter_args.positions if "!" not in pl}
        misses = {int(pl[0]) - 1: pl[2:] for pl in filter_args.positions if "!" in pl}
        filtered_words = filter(
            lambda w: all([w[k] == v for k, v in exact_matches.items()])
            and all([w[k] not in v for k, v in misses.items()]),
            filtered_words,
        )
    if filter_args.exclude_words:
        filtered_words = filter(lambda w: all([w != exwd.lower() for exwd in filter_args.exclude_words]), filtered_words)
    if filter_args.no_repeats:
        filtered_words = filter(lambda w: len(set(w)) == 5, filtered_words)
    if filter_args.no_plurals:
        filtered_words = filter(lambda w: not w.endswith("s") or w.endswith("ss"), filtered_words)
    if filter_args.no_past_tense:
        filtered_words = filter(
            lambda w: not w.endswith("ed") or (w.endswith("eed") and w not in ["freed"]) or w in ["unwed", "embed"],
            filtered_words,
        )
    return set(filtered_words)


def print_stats(word_list: Iterable, positional_ranking_filter):
    # Rank letter occurrence among all words
    merged_words = "".join(word_list)
    distinct_letters = set(merged_words)
    letter_stats = {l: merged_words.count(l) for l in distinct_letters}
    letter_stats_ranked = {k: v for k, v in sorted(letter_stats.items(), reverse=True, key=lambda item: item[1])}

    print("==== WORD LIST STATS ====")
    print(
        f"DISTRIBUTION FOR {sum(letter_stats_ranked.values())} LETTER OCCURRENCES \n"
        f"ACROSS {len(word_list)} MATCHING WORDS:"
    )
    print("LETTER  OCCURRENCE")
    [print(f"     {k}  {v}") for k, v in letter_stats_ranked.items()]
    print("POSITION  RANKED LETTER FREQUENCY")

    # Rank letter occurrence per position
    position_rankings = {}
    for p in range(1, 6):
        p_letters = [w[p - 1] for w in word_list]
        distinct_p_letters = set(p_letters)
        p_letter_stats = {l: p_letters.count(l) for l in distinct_p_letters}
        p_letter_stats_ranked = {
            k: v for k, v in sorted(p_letter_stats.items(), reverse=True, key=lambda item: item[1])
        }
        position_rankings[p] = p_letter_stats_ranked
        print(f"{p}  {p_letter_stats_ranked}")
    if positional_ranking_filter:
        if positional_ranking_filter == "*":
            positional_ranking_filter = ''.join(letter_stats_ranked.keys())
        print("   |", end="")
        for p in range(1, 6):
            print(f" {str(p).rjust(3,' ') } |", end="")
        print("")
        for l in positional_ranking_filter:
            print(f" {l.upper()} |", end="")
            for p in range(1, 6):
                print(f" {str(position_rankings[p].get(l, '-')).rjust(3, ' ')} |", end="")
            print("")


def pick_next_guess(args: argparse.Namespace, filtered_words: List[str]):
    """Of the final words filtered down, pick one of the filtered words that will best narrow down options"""
    ranked_guesses_to_print = args.pick_next_guess or args.G or args.Gx
    guesses = five_letter_word_set.US_WORDS
    if args.G:
        guesses = filtered_words.copy()
    if args.Gx:
        guesses = filter_words(word_set=five_letter_word_set.US_WORDS, filter_args=args)
    guessers = {}
    guess_results = {}
    num_guesses = len(guesses)
    guessing_start_time = datetime.now()
    for guess_num, guess in enumerate(guesses, start=1):
        guess_progress_msg = ""
        if num_guesses > 50:
            guess_progress_msg = f"Processing guess {str(guess_num).rjust(len(str(num_guesses)))}/{num_guesses}, guess={guess.upper()}, avg={(datetime.now() - guessing_start_time).total_seconds()/guess_num:.4f}s"
            print(guess_progress_msg + "         \r", end="")
        simulated_answers = filtered_words.copy()
        if guess in simulated_answers:
            simulated_answers.remove(guess)  # this one is known to be an exact match
        guess_results[guess] = {}

        # Run a simulation for a chosen answer,
        # and gather results on how each guess performs in the simulation
        num_answers = len(simulated_answers)
        simulation_start_time = datetime.now()
        for answer_num, answer in enumerate(simulated_answers, start=1):
            if num_guesses > 50:
                answer_progress_msg = f"Answer {str(answer_num).rjust(len(str(num_answers)))}/{num_answers}, answer={answer.upper()}, avg={(datetime.now() - simulation_start_time).total_seconds()/answer_num:.4f}s"
                print(guess_progress_msg + " | " + answer_progress_msg + "         \r", end="")
            # Get or set the WordleGuesser instance by key=answer
            if answer in guessers:
                guesser = guessers[answer]
            else:
                guesser = WordleGuesser(provided_answer=answer)
                guessers[answer] = guesser
            guesser.store_guess(guess)
            args_copy = copy.deepcopy(args)
            # so we don't re-evaluate on an internal simluation run
            args_copy.pick_next_guess = False
            args_copy.G = False
            args_copy.Gx = False
            for i, letter_and_score in guesser.guess_history[guess].items():
                pos = i+1
                letter = letter_and_score[0]
                score = letter_and_score[1]

                # Augment the args_copy spec based on match results of this guess for the chosen answer
                if score == 0:  # letter not in this answer
                    # ONLY! add it to "not_contains", if it is NOT already in the "all" (from a previous guess, or previous letter in this guess)
                    # otherwise they contradict each other
                    if not args_copy.all or letter not in args_copy.all:
                        args_copy.not_contains = ''.join(set(args_copy.not_contains+letter)) if args_copy.not_contains else letter
                    old_p = list(filter(lambda x: x.startswith(str(pos)), args_copy.positions or []))
                    new_p = f"{pos}!{letter}"
                    if old_p:
                        args_copy.positions.remove(old_p[0])
                        new_p = old_p[0] + letter
                    args_copy.positions = args_copy.positions + [new_p] if args_copy.positions else [new_p]
                elif score == 1:  # letter in answer, but not in this position
                    args_copy.all = ''.join(set(args_copy.all+letter)) if args_copy.all else letter
                    # Must now remove it from "not_contains" if it exists there (from a previous guess, or previous letter in this guess)
                    if args_copy.not_contains and letter in args_copy.not_contains:
                        args_copy.not_contains = args_copy.not_contains.replace(letter, "")
                    old_p = list(filter(lambda x: x.startswith(str(pos)), args_copy.positions or [])) 
                    new_p = f"{pos}!{letter}"
                    if old_p:
                        args_copy.positions.remove(old_p[0])
                        new_p = old_p[0] + letter
                    args_copy.positions = args_copy.positions + [new_p] if args_copy.positions else [new_p]
                elif score == 2:  # letter in answer, in this position
                    args_copy.all = ''.join(set(args_copy.all+letter)) if args_copy.all else letter
                    # Must now remove it from "not_contains" if it exists there (from a previous guess, or previous letter in this guess)
                    if args_copy.not_contains and letter in args_copy.not_contains:
                        args_copy.not_contains = args_copy.not_contains.replace(letter, "")
                    old_p = list(filter(lambda x: x.startswith(str(pos)), args_copy.positions or [])) 
                    if old_p:
                        args_copy.positions.remove(old_p[0])
                    new_p = f"{pos}{letter}"
                    args_copy.positions = args_copy.positions + [new_p] if args_copy.positions else [new_p]
            results = filter_words(word_set=simulated_answers, filter_args=args_copy)
            # Use below for debugging
            #print(f"DEBUG: answer={answer}:guess={guess}->words={simulated_answers}\n\t@{args_copy}\n\t=results:{results}")
            guess_results[guess][answer] = sorted(results)
    print("", end="")
    print("")

    def score_guess(guess_item):
        guess_results_for_each_answer = guess_item[1]
        if not guess_results_for_each_answer:  # empty list
            return 0
        answers_simulated = len(guess_results_for_each_answer)
        total_results_for_all_answers = sum([len(results_for_answer) for results_for_answer in guess_results_for_each_answer.values()])
        avg_results_per_answer = total_results_for_all_answers / answers_simulated
        return avg_results_per_answer

    print("==== NEXT GUESS WORD RANKING ====")
    if args.show_next_guess_results:
        scored_guess_results = {item[0]: {"score": round(score_guess(item), 2), "results_for_answer": item[1]} for item in guess_results.items()}
    else:
        scored_guess_results = {item[0]: {"score": round(score_guess(item), 2)} for item in guess_results.items()}
    ranked_guess_results = sorted(scored_guess_results.items(), key=lambda item: item[1]["score"])
    top_ranked_guess_results = OrderedDict(itertools.islice(ranked_guess_results, ranked_guesses_to_print))
    pprint(top_ranked_guess_results)

if __name__ == "__main__":
    print("Enter filter spec (or -h for help):")
    for line in sys.stdin:
        spec = line.rstrip()
        args = parse_filter_spec(spec)
        print(args)
        if args.expanded_word_list:
            words_to_use = five_letter_word_set.US_WORDS
            print(f"Using US_WORDS set of {len(words_to_use)} words")
        else:
            words_to_use = five_letter_word_set.CURATED_LIKELY_WORDS
            print(f"Using CURATED_LIKELY_WORDS set of {len(words_to_use)} words")
        final_words = filter_words(words_to_use, args)
        print(f"\n==== {len(final_words)} MATCHES ====")
        [print(w) for w in sorted(final_words)]
        print_stats(final_words, args.positional_ranking_matrix)
        if sum(map(bool, [args.pick_next_guess, args.G, args.Gx])) > 2:
            print("Error: Pick one of -g or -G or --Gx")
            sys.exit(1)
        if args.pick_next_guess or args.G or args.Gx:
            pick_next_guess(args, final_words)
        print(f"==== FOR {len(final_words)} MATCHES ====")
