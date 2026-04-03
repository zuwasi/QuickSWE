#include "tokenizer.h"
#include <string.h>
#include <stdio.h>

TokenResult *tokenize(const char *input, char delimiter) {
    if (!input) return NULL;

    TokenResult *result = (TokenResult *)malloc(sizeof(TokenResult));
    if (!result) return NULL;

    /* Count delimiters to estimate token count */
    size_t max_tokens = 1;
    for (const char *p = input; *p; p++) {
        if (*p == delimiter) max_tokens++;
    }

    result->tokens = (char **)malloc(max_tokens * sizeof(char *));
    if (!result->tokens) {
        free(result);
        return NULL;
    }
    result->count = 0;

    const char *start = input;
    const char *p = input;

    while (1) {
        if (*p == delimiter || *p == '\0') {
            /* Extract token from start to p */
            size_t len = p - start;
            char *token = (char *)malloc(len + 1);
            if (!token) {
                tokenresult_free(result);
                return NULL;
            }
            memcpy(token, start, len);
            token[len] = '\0';
            result->tokens[result->count++] = token;

            if (*p == '\0') break;
            start = p + 1;
        }
        /*
         * BUG/MISSING FEATURE: No handling of backslash escaping.
         * A '\' before the delimiter should prevent splitting.
         *
         * BUG/MISSING FEATURE: No handling of quoted strings.
         * Content inside "..." should be treated as literal.
         *
         * Currently, this tokenizer treats every occurrence of the
         * delimiter as a split point, regardless of context.
         */
        p++;
    }

    return result;
}

void tokenresult_free(TokenResult *result) {
    if (!result) return;
    if (result->tokens) {
        for (size_t i = 0; i < result->count; i++) {
            free(result->tokens[i]);
        }
        free(result->tokens);
    }
    free(result);
}
