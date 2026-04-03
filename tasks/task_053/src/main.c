#include <stdio.h>
#include <string.h>
#include "tokenizer.h"

static void print_tokens(TokenResult *result) {
    if (!result) {
        printf("NULL\n");
        return;
    }
    printf("COUNT: %zu\n", result->count);
    for (size_t i = 0; i < result->count; i++) {
        printf("TOKEN[%zu]: [%s]\n", i, result->tokens[i]);
    }
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <test_name>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "simple_split") == 0) {
        TokenResult *r = tokenize("hello,world,foo", ',');
        print_tokens(r);
        tokenresult_free(r);

    } else if (strcmp(argv[1], "escaped_delimiter") == 0) {
        /* Input: hello\,world,foo  -- the \, should NOT split */
        TokenResult *r = tokenize("hello\\,world,foo", ',');
        print_tokens(r);
        tokenresult_free(r);

    } else if (strcmp(argv[1], "quoted_string") == 0) {
        /* Input: "a,b",c  -- the comma inside quotes should NOT split */
        TokenResult *r = tokenize("\"a,b\",c", ',');
        print_tokens(r);
        tokenresult_free(r);

    } else if (strcmp(argv[1], "escaped_backslash") == 0) {
        /* Input: hello\\,world  -- \\ is literal backslash, then comma splits */
        TokenResult *r = tokenize("hello\\\\,world", ',');
        print_tokens(r);
        tokenresult_free(r);

    } else if (strcmp(argv[1], "empty_tokens") == 0) {
        /* Input: a,,b  -- empty token between commas */
        TokenResult *r = tokenize("a,,b", ',');
        print_tokens(r);
        tokenresult_free(r);

    } else if (strcmp(argv[1], "mixed") == 0) {
        /* Input: "x,y",a\,b,c  -- quoted and escaped in same input */
        TokenResult *r = tokenize("\"x,y\",a\\,b,c", ',');
        print_tokens(r);
        tokenresult_free(r);

    } else {
        printf("Unknown test: %s\n", argv[1]);
        return 1;
    }

    return 0;
}
