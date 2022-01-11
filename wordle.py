# pyre-strict

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Set, Optional, Tuple
from itertools import product
from tqdm import tqdm


LENGTH = 5


class HintType(Enum):
    GREEN = "g"
    YELLOW = "y"
    BLACK = "b"


POSSIBLE_GUESS_RESULTS: List[str] = [
    "".join(x)
    for x in product(
        *[[HintType.YELLOW.value, HintType.BLACK.value, HintType.GREEN.value]] * LENGTH
    )
]


with open("wordlist.txt") as fi:
    CORPUS: Set[str] = set(fi.read().split())


@dataclass
class Prompt:
    idx: int
    letter: str
    hint_type: HintType


@dataclass
class Hint:
    min_count: int
    max_count: int
    indexes: Tuple[Optional[bool]]

    def __copy__(self) -> "Hint":
        return Hint(self.min_count, self.max_count, self.indexes)

    @classmethod
    def parse_guess(cls, word: str, colors: str) -> Dict[str, "Hint"]:
        guess = [Prompt(i, word[i], HintType(colors[i])) for i in range(LENGTH)]
        hints = {}
        for letter in {prompt.letter for prompt in guess}:
            prompts = [pr for pr in guess if pr.letter == letter]

            # Get valid count range
            hint_type_counts = Counter([pr.hint_type for pr in prompts])
            min_count = (
                hint_type_counts[HintType.GREEN] + hint_type_counts[HintType.YELLOW]
            )
            max_count = min_count if hint_type_counts[HintType.BLACK] != 0 else LENGTH

            # Get valid indexes
            indexes: List[Optional[bool]] = [None for _ in range(LENGTH)]
            for pr in prompts:
                indexes[pr.idx] = pr.hint_type == HintType.GREEN

            hints[letter] = Hint(min_count, max_count, tuple(indexes))

        return hints

    def _merge_with(self, other: "Hint") -> "Hint":
        min_count = max(self.min_count, other.min_count)
        max_count = min(self.max_count, other.max_count)
        indexes = tuple(
            map(
                lambda x: x[0] if x[1] == None else x[1],
                zip(self.indexes, other.indexes),
            )
        )
        return Hint(min_count, max_count, indexes)

    @classmethod
    def merge_hints(
        cls, left_hints: Dict[str, "Hint"], right_hints: Dict[str, "Hint"]
    ) -> Dict[str, "Hint"]:
        new_hints = left_hints.copy()
        for letter in right_hints:
            if letter not in new_hints:
                new_hints[letter] = right_hints[letter]
            else:
                new_hints[letter] = new_hints[letter]._merge_with(right_hints[letter])
        return new_hints

    def check_word(self, letter: str, word: str) -> bool:
        if not self.min_count <= word.count(letter) <= self.max_count:
            return False
        for idx, is_present in enumerate(self.indexes):
            if is_present == True and word[idx] != letter:
                return False
            if is_present == False and word[idx] == letter:
                return False
        return True


class GameInfo:
    def __init__(self, words: Set[str], hints: Dict[str, Hint]) -> None:
        self.words = words
        self.hints = hints

    def apply_hints(self, guess: Dict[str, Hint]) -> "GameInfo":
        # Merge into existing hints
        new_hints = Hint.merge_hints(self.hints, guess)

        # Filter words
        new_words = self.words.copy()
        for letter, hint in new_hints.items():
            new_words = {w for w in new_words if hint.check_word(letter, w)}

        return GameInfo(new_words, new_hints)

    def suggest_guess(self) -> str:
        return min(
            tqdm(self.words),
            key=lambda word: max(
                len(self.apply_hints(Hint.parse_guess(word, guess_result)).words)
                for guess_result in POSSIBLE_GUESS_RESULTS
            ),
        )


if __name__ == "__main__":
    game_info = GameInfo(CORPUS, {})
    word = 'soare'

    while True:
        print('Try:', word)
        colors = input("Enter colors > ")
        guess = Hint.parse_guess(word, colors)
        game_info = game_info.apply_hints(guess)
        print(" ".join(game_info.words))
        print(len(game_info.words), "words left")
        if len(game_info.words) <= 1:
            break
        word = game_info.suggest_guess()
