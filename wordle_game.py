import random
import sys
import five_letter_word_set


class WordleGuesser:
    def __init__(self, provided_answer=None):
        self.answer = provided_answer
        self.guess_history = {}

    def reveal_answer(self):
        print(f"The answer was set to {self.answer}")

    def prompt_guess(self):
        print(f"\n{len(self.guess_history)+1}|Make a guess: ")

    def take_guesses(self):
        self.prompt_guess()
        for line in sys.stdin:
            guess = line.rstrip().upper()
            if guess in ["Q", "QUIT", "EXIT"]:
                print("Bye Bye.")
                break
            if guess in self.guess_history:
                print(f'Already guessed "{guess}". Try another guess.')
                continue
            # Use ! at end of guess to override poor dictionary
            if (
                not guess.endswith("!")
                and guess.lower() not in five_letter_word_set.US_WORDS
            ):
                print(f'Unrecognized word guessed: "{guess}". Try another guess.')
                continue
            if guess.endswith("!"):
                guess = guess[0:-1]
            self.store_guess(guess)
            self.print_guess_results()
            if guess == self.answer:
                print(f"✅ YOU GOT IT! ==> {self.answer} in {len(self.guess_history)}/6")
                break
            if len(self.guess_history) >= 6:
                print("❌ Sorry. Out of guesses :(")
                break
            self.prompt_guess()

    def store_guess(self, guess):
        letter_scores = {}
        # Need to do breadth-first search.
        # i.e. full pass for exact matches
        # 2nd full pass for misplaced matches
        for i, letter in enumerate(guess):
            score = self.eval_letter(i, letter)
            if score == 2:
                letter_scores[i] = (letter, score)
        for i, letter in enumerate(guess):
            if i in letter_scores:
                continue  # already marked this letter an exact match
            score = self.eval_letter(i, letter)
            if score == 1:
                # Only keep it marked 1 if the occurrence of this letter in the word is greater than
                # the exact matches and misplaced matches so far on this letter from the given guess
                letter_occurrence = sum(1 for ans_letter in self.answer if ans_letter == letter)
                exact_guesses = sum(1 for ls in letter_scores.values() if ls[0] == letter and ls[1] == 2)
                misplaced_guesses_so_far = sum(1 for ls in letter_scores.values() if ls[0] == letter and ls[1] == 1)
                saved_score = 1 if letter_occurrence > (exact_guesses + misplaced_guesses_so_far) else 0
                letter_scores[i] = (letter, saved_score)
            else:
                letter_scores[i] = (letter, 0)
        self.guess_history[guess] = {k: letter_scores[k] for k in sorted(letter_scores)}

    def print_guess_results(self):
        for g in self.guess_history.keys():
            result = ""
            for i, letter_and_score in self.guess_history[g].items():
                letter = letter_and_score[0]
                score = letter_and_score[1]
                if score == 0:
                    result += f" {letter} "
                elif score == 1:
                    result += f"[{letter}]"
                elif score == 2:
                    result += f"({letter})"
            print("\t" + result)

    def eval_letter(self, index, letter):
        answer_letter = self.answer[index]
        if letter == answer_letter:
            return 2
        if letter in self.answer:
            return 1
        return 0


if __name__ == "__main__":
    given_word = sys.argv[1] if len(sys.argv) > 1 else None
    answer = None
    if not given_word:
        # fiver_letter_words = [w for w in five_letter_word_set.US_WORDS if len(w) == 5]
        fiver_letter_words = list(five_letter_word_set.CURATED_LIKELY_WORDS)
        rnd_idx = random.randint(0, len(fiver_letter_words) - 1)
        answer = fiver_letter_words[rnd_idx].upper()
        wordle = WordleGuesser(answer)
        wordle.take_guesses()
    else:
        if len(given_word) != 5:
            raise ValueError("Word length must be 5 letters")
        if given_word.lower() not in five_letter_word_set.US_WORDS:
            raise ValueError(f"Unrecognized word: {given_word.upper()}")
        answer = given_word.upper()
        wordle = WordleGuesser(answer)
        wordle.take_guesses()
