#pragma once
#include <string>
#include <vector>

class Tokenizer {
public:
    static std::vector<std::string> split(const std::string& input, char delimiter) {
        std::vector<std::string> tokens;
        std::string current;
        bool escaped = false;

        for (std::size_t i = 0; i < input.size(); ++i) {
            if (escaped) {
                current += input[i];
                escaped = false;
            } else if (input[i] == '\\') {
                escaped = true;
            } else if (input[i] == delimiter) {
                tokens.push_back(current);
                current.clear();
            } else {
                current += input[i];
            }
        }
        tokens.push_back(current);
        return tokens;
    }

    static std::string join(const std::vector<std::string>& tokens, char delimiter) {
        std::string result;
        for (std::size_t i = 0; i < tokens.size(); ++i) {
            if (i > 0) result += delimiter;
            result += tokens[i];
        }
        return result;
    }

    static std::string escape(const std::string& input, char delimiter) {
        std::string result;
        for (char c : input) {
            if (c == delimiter) {
                result += '\\';
            }
            result += c;
        }
        return result;
    }

    static int count_tokens(const std::string& input, char delimiter) {
        return static_cast<int>(split(input, delimiter).size());
    }
};
