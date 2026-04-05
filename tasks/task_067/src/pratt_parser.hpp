#pragma once
#include <string>
#include <vector>
#include <stdexcept>
#include <cmath>
#include <cctype>

class PrattParser {
    enum class TokenType { NUMBER, PLUS, MINUS, STAR, SLASH, CARET, LPAREN, RPAREN, END };

    struct Token {
        TokenType type;
        double value;
    };

public:
    double parse(const std::string& expr) {
        tokens_.clear();
        pos_ = 0;
        tokenize(expr);
        double result = parse_expr(0);
        expect(TokenType::END);
        return result;
    }

private:
    std::vector<Token> tokens_;
    std::size_t pos_;

    void tokenize(const std::string& s) {
        std::size_t i = 0;
        while (i < s.size()) {
            if (std::isspace(s[i])) { ++i; continue; }
            if (std::isdigit(s[i]) || s[i] == '.') {
                std::size_t start = i;
                while (i < s.size() && (std::isdigit(s[i]) || s[i] == '.')) ++i;
                tokens_.push_back({TokenType::NUMBER, std::stod(s.substr(start, i - start))});
            } else {
                TokenType t;
                switch (s[i]) {
                    case '+': t = TokenType::PLUS; break;
                    case '-': t = TokenType::MINUS; break;
                    case '*': t = TokenType::STAR; break;
                    case '/': t = TokenType::SLASH; break;
                    case '^': t = TokenType::CARET; break;
                    case '(': t = TokenType::LPAREN; break;
                    case ')': t = TokenType::RPAREN; break;
                    default: throw std::runtime_error("unexpected char");
                }
                tokens_.push_back({t, 0});
                ++i;
            }
        }
        tokens_.push_back({TokenType::END, 0});
    }

    Token peek() const { return tokens_[pos_]; }
    Token advance() { return tokens_[pos_++]; }

    void expect(TokenType t) {
        if (peek().type != t) throw std::runtime_error("unexpected token");
        advance();
    }

    int prefix_bp(TokenType t) {
        if (t == TokenType::MINUS) return 5;
        return -1;
    }

    int infix_bp_left(TokenType t) {
        switch (t) {
            case TokenType::PLUS: case TokenType::MINUS: return 1;
            case TokenType::STAR: case TokenType::SLASH: return 1;
            case TokenType::CARET: return 5;
            default: return -1;
        }
    }

    int infix_bp_right(TokenType t) {
        switch (t) {
            case TokenType::PLUS: case TokenType::MINUS: return 2;
            case TokenType::STAR: case TokenType::SLASH: return 2;
            case TokenType::CARET: return 6;
            default: return -1;
        }
    }

    double parse_expr(int min_bp) {
        Token tok = advance();
        double left;

        if (tok.type == TokenType::NUMBER) {
            left = tok.value;
        } else if (tok.type == TokenType::LPAREN) {
            left = parse_expr(0);
            expect(TokenType::RPAREN);
        } else if (tok.type == TokenType::MINUS) {
            int bp = prefix_bp(TokenType::MINUS);
            left = -parse_expr(bp);
        } else {
            throw std::runtime_error("unexpected token in prefix position");
        }

        while (true) {
            Token op = peek();
            int lbp = infix_bp_left(op.type);
            if (lbp < 0 || lbp < min_bp) break;
            advance();
            int rbp = infix_bp_right(op.type);
            double right = parse_expr(rbp);
            switch (op.type) {
                case TokenType::PLUS:  left += right; break;
                case TokenType::MINUS: left -= right; break;
                case TokenType::STAR:  left *= right; break;
                case TokenType::SLASH: left /= right; break;
                case TokenType::CARET: left = std::pow(left, right); break;
                default: break;
            }
        }
        return left;
    }
};
