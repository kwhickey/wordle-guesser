"""Filters to narrow down a set of 5-letter-words"""
import argparse
import sys
import re

from typing import Iterable

import five_letter_word_set


def parse_filter_spec(spec: str):
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
        help="all of teh provided letters appear one or more times in the word, "
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
        filtered_words = filter(lambda w: all([l in w for l in filter_args.all]), filtered_words)
    if filter_args.positions:
        exact_matches = {int(pl[0]) - 1: pl[1] for pl in filter_args.positions if "!" not in pl}
        misses = {int(pl[0]) - 1: pl[2:] for pl in filter_args.positions if "!" in pl}
        filtered_words = filter(
            lambda w: all([w[k] == v for k, v in exact_matches.items()])
            and all([w[k] not in v for k, v in misses.items()]),
            filtered_words,
        )
    return set(filtered_words)


def print_stats(word_list: Iterable):
    # Rank letter occurrence among all words
    merged_words = "".join(word_list)
    distinct_letters = set(merged_words)
    letter_stats = {l: merged_words.count(l) for l in distinct_letters}
    letter_stats_ranked = {k: v for k, v in sorted(letter_stats.items(), reverse=True, key=lambda item: item[1])}

    print("==== WORD LIST STATS ====")
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


if __name__ == "__main__":
    print("Enter filter spec (or -h for help):")
    for line in sys.stdin:
        spec = line.rstrip()
        args = parse_filter_spec(spec)
        print(args)
        final_words = filter_words(five_letter_word_set.US_WORDS, args)
        print(f"\n==== {len(final_words)} MATCHES ====")
        [print(w) for w in sorted(final_words)]
        print_stats(final_words)
