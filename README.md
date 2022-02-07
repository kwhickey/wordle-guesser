Wordle Guesser
====

_Console-based Wordle gameplay and tool to help filter-down Worle candidate words_


## Playing Wordle
_To play with a random word, run:_

```shell
python3 five_letter_word_filters.py
```

_To play with a word you supply, run:_

```shell
python3 five_letter_word_filters.py
```

_Example output:_

```
〉python wordle_game.py prize 

1|Make a guess: 
train
	 T (R) A [I] N 

2|Make a guess: 
cried
	 T (R) A [I] N 
	 C (R)(I)[E] D 

3|Make a guess: 
prime
	 T (R) A [I] N 
	 C (R)(I)[E] D 
	(P)(R)(I) M (E)

4|Make a guess: 
prize
	 T (R) A [I] N 
	 C (R)(I)[E] D 
	(P)(R)(I) M (E)
	(P)(R)(I)(Z)(E)
✅ YOU GOT IT! ==> PRIZE in 4/6
```

## Filtering Words
_Run:_

```shell
python3 five_letter_word_filters.py
``` 

_Example output:_

```
〉python five_letter_word_filters.py
Enter filter spec (or -h for help):
-n tandc -p 2r 4!ie 3i -a e
Namespace(all='e', contains=None, ends=None, not_contains='tandc', positions=['2r', '4!ie', '3i'], starts=None)

==== 7 MATCHES ====
bribe
frise
grime
gripe
prime
prise
prize
==== WORD LIST STATS ====
LETTER  OCCURRENCE
     e  7
     i  7
     r  7
     p  4
     s  2
     b  2
     m  2
     g  2
     z  1
     f  1
POSITION  RANKED LETTER FREQUENCY
1  {'p': 3, 'g': 2, 'f': 1, 'b': 1}
2  {'r': 7}
3  {'i': 7}
4  {'s': 2, 'm': 2, 'b': 1, 'z': 1, 'p': 1}
5  {'e': 7}

``` 
