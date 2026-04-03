#ifndef TOKENIZER_H
#define TOKENIZER_H

#include <stdlib.h>

typedef struct {
    char **tokens;
    size_t count;
} TokenResult;

/*
 * Split input string by delimiter character.
 * Returns a TokenResult with an array of token strings and count.
 * Caller must free the result with tokenresult_free().
 */
TokenResult *tokenize(const char *input, char delimiter);

/* Free a TokenResult and all its tokens. */
void tokenresult_free(TokenResult *result);

#endif /* TOKENIZER_H */
