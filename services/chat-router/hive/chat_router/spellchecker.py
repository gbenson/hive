from functools import lru_cache
from typing import Optional

from spellchecker import SpellChecker as _SpellChecker
from spellchecker.utils import KeyT


class SpellChecker(_SpellChecker):
    def candidates(self, word: KeyT) -> Optional[set[str]]:
        if (result := self._candidates(word)):
            return result.copy()
        return None

    @lru_cache(maxsize=16384)
    def _candidates(self, word: KeyT) -> Optional[set[str]]:
        return super().candidates(word)


spellcheck = SpellChecker()
