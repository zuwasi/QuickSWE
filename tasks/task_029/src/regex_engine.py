"""
Simple regex engine with backtracking support.

Supports: literal chars, '.', '*', '+', '?', grouping with '(' and ')',
character classes [abc], anchors ^ and $.
"""

from typing import Optional, List, Tuple


class RegexToken:
    """Represents a parsed regex token."""

    LITERAL = "LITERAL"
    DOT = "DOT"
    STAR = "STAR"
    PLUS = "PLUS"
    QUESTION = "QUESTION"
    GROUP = "GROUP"
    CHAR_CLASS = "CHAR_CLASS"
    ANCHOR_START = "ANCHOR_START"
    ANCHOR_END = "ANCHOR_END"

    def __init__(self, token_type: str, value=None, children=None):
        self.token_type = token_type
        self.value = value
        self.children = children or []

    def __repr__(self):
        return f"Token({self.token_type}, {self.value!r})"


class RegexParser:
    """Parses a regex pattern string into a list of tokens."""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0

    def parse(self) -> List[RegexToken]:
        tokens = []
        while self.pos < len(self.pattern):
            tokens.append(self._parse_atom())
        return tokens

    def _parse_atom(self) -> RegexToken:
        ch = self.pattern[self.pos]

        if ch == '^':
            self.pos += 1
            return RegexToken(RegexToken.ANCHOR_START)

        if ch == '$':
            self.pos += 1
            return RegexToken(RegexToken.ANCHOR_END)

        if ch == '.':
            self.pos += 1
            base = RegexToken(RegexToken.DOT)
            return self._apply_quantifier(base)

        if ch == '(':
            self.pos += 1
            children = []
            while self.pos < len(self.pattern) and self.pattern[self.pos] != ')':
                children.append(self._parse_atom())
            if self.pos < len(self.pattern):
                self.pos += 1
            group = RegexToken(RegexToken.GROUP, children=children)
            return self._apply_quantifier(group)

        if ch == '[':
            self.pos += 1
            chars = []
            while self.pos < len(self.pattern) and self.pattern[self.pos] != ']':
                chars.append(self.pattern[self.pos])
                self.pos += 1
            if self.pos < len(self.pattern):
                self.pos += 1
            base = RegexToken(RegexToken.CHAR_CLASS, value=chars)
            return self._apply_quantifier(base)

        self.pos += 1
        base = RegexToken(RegexToken.LITERAL, value=ch)
        return self._apply_quantifier(base)

    def _apply_quantifier(self, base: RegexToken) -> RegexToken:
        if self.pos < len(self.pattern):
            ch = self.pattern[self.pos]
            if ch == '*':
                self.pos += 1
                return RegexToken(RegexToken.STAR, children=[base])
            elif ch == '+':
                self.pos += 1
                return RegexToken(RegexToken.PLUS, children=[base])
            elif ch == '?':
                self.pos += 1
                return RegexToken(RegexToken.QUESTION, children=[base])
        return base


class RegexMatcher:
    """Matches a parsed regex against an input string using backtracking."""

    def __init__(self, tokens: List[RegexToken], timeout_steps: int = 100000):
        self.tokens = tokens
        self.timeout_steps = timeout_steps
        self._steps = 0

    def match(self, text: str) -> Optional[Tuple[int, int]]:
        anchored_start = (self.tokens and
                          self.tokens[0].token_type == RegexToken.ANCHOR_START)
        tokens = self.tokens[1:] if anchored_start else self.tokens

        if anchored_start:
            end = self._match_at(tokens, text, 0)
            if end is not None:
                return (0, end)
            return None

        for start in range(len(text) + 1):
            self._steps = 0
            end = self._match_at(tokens, text, start)
            if end is not None:
                return (start, end)
        return None

    def _match_at(self, tokens: List[RegexToken], text: str,
                  pos: int) -> Optional[int]:
        return self._match_tokens(tokens, 0, text, pos)

    def _match_tokens(self, tokens: List[RegexToken], tok_idx: int,
                      text: str, pos: int) -> Optional[int]:
        self._steps += 1
        if self._steps > self.timeout_steps:
            raise TimeoutError("Regex matching exceeded step limit")

        if tok_idx >= len(tokens):
            return pos

        token = tokens[tok_idx]

        if token.token_type == RegexToken.ANCHOR_END:
            if pos == len(text):
                return self._match_tokens(tokens, tok_idx + 1, text, pos)
            return None

        if token.token_type == RegexToken.LITERAL:
            if pos < len(text) and text[pos] == token.value:
                return self._match_tokens(tokens, tok_idx + 1, text, pos + 1)
            return None

        if token.token_type == RegexToken.DOT:
            if pos < len(text):
                return self._match_tokens(tokens, tok_idx + 1, text, pos + 1)
            return None

        if token.token_type == RegexToken.CHAR_CLASS:
            if pos < len(text) and text[pos] in token.value:
                return self._match_tokens(tokens, tok_idx + 1, text, pos + 1)
            return None

        if token.token_type == RegexToken.GROUP:
            end = self._match_tokens(token.children, 0, text, pos)
            if end is not None:
                return self._match_tokens(tokens, tok_idx + 1, text, end)
            return None

        if token.token_type == RegexToken.STAR:
            return self._match_star(token.children[0], tokens, tok_idx, text, pos)

        if token.token_type == RegexToken.PLUS:
            return self._match_plus(token.children[0], tokens, tok_idx, text, pos)

        if token.token_type == RegexToken.QUESTION:
            return self._match_question(token.children[0], tokens, tok_idx, text, pos)

        return None

    def _match_star(self, child: RegexToken, tokens: List[RegexToken],
                    tok_idx: int, text: str, pos: int) -> Optional[int]:
        positions = [pos]
        current = pos
        while current <= len(text):
            next_pos = self._match_single(child, text, current)
            if next_pos is None or next_pos == current:
                break
            positions.append(next_pos)
            current = next_pos

        for try_pos in reversed(positions):
            result = self._match_tokens(tokens, tok_idx + 1, text, try_pos)
            if result is not None:
                return result
        return None

    def _match_plus(self, child: RegexToken, tokens: List[RegexToken],
                    tok_idx: int, text: str, pos: int) -> Optional[int]:
        positions = []
        current = pos
        while current <= len(text):
            self._steps += 1
            if self._steps > self.timeout_steps:
                raise TimeoutError("Regex matching exceeded step limit")
            next_pos = self._match_single(child, text, current)
            if next_pos is None:
                break
            positions.append(next_pos)
            current = next_pos

        if not positions:
            return None

        for try_pos in reversed(positions):
            result = self._match_tokens(tokens, tok_idx + 1, text, try_pos)
            if result is not None:
                return result
        return None

    def _match_question(self, child: RegexToken, tokens: List[RegexToken],
                        tok_idx: int, text: str, pos: int) -> Optional[int]:
        next_pos = self._match_single(child, text, pos)
        if next_pos is not None:
            result = self._match_tokens(tokens, tok_idx + 1, text, next_pos)
            if result is not None:
                return result
        return self._match_tokens(tokens, tok_idx + 1, text, pos)

    def _match_single(self, token: RegexToken, text: str,
                      pos: int) -> Optional[int]:
        if token.token_type == RegexToken.LITERAL:
            if pos < len(text) and text[pos] == token.value:
                return pos + 1
        elif token.token_type == RegexToken.DOT:
            if pos < len(text):
                return pos + 1
        elif token.token_type == RegexToken.CHAR_CLASS:
            if pos < len(text) and text[pos] in token.value:
                return pos + 1
        elif token.token_type == RegexToken.GROUP:
            return self._match_tokens(token.children, 0, text, pos)
        return None


def regex_match(pattern: str, text: str,
                timeout: int = 100000) -> Optional[Tuple[int, int]]:
    parser = RegexParser(pattern)
    tokens = parser.parse()
    matcher = RegexMatcher(tokens, timeout_steps=timeout)
    return matcher.match(text)


def regex_search(pattern: str, text: str) -> bool:
    return regex_match(pattern, text) is not None


def regex_find_all(pattern: str, text: str) -> List[str]:
    results = []
    start = 0
    while start <= len(text):
        m = regex_match(pattern, text[start:])
        if m is None:
            break
        s, e = m
        if e > s:
            results.append(text[start + s:start + e])
            start += s + max(1, e - s)
        else:
            start += 1
    return results
