#pragma once
#include <vector>
#include <functional>
#include <type_traits>

// Sum all arguments
template <typename... Args>
auto sum_all(Args... args) {
    return (args + ...);
}

// Check if all arguments are truthy
template <typename... Args>
bool all_of(Args... args) {
    return (args || ...);
}

// Check if any argument is truthy
template <typename... Args>
bool any_of(Args... args) {
    return (args && ...);
}

// Apply a transformation to each argument and sum results
template <typename F, typename First, typename... Rest>
auto transform_reduce(F func, First first, Rest... rest) {
    if constexpr (sizeof...(rest) == 0) {
        return func(first);
    } else {
        return func(first) + transform_reduce(func, rest...);
    }
}

// Apply function to each argument and collect in vector
template <typename F, typename... Args>
auto apply_to_each(F func, Args... args) {
    using R = std::invoke_result_t<F, std::common_type_t<Args...>>;
    std::vector<R> result;
    result.reserve(sizeof...(args));
    auto collector = [&result, &func](auto arg) {
        result.push_back(func(arg));
        return 0;
    };
    (collector(args), ...);
    return result;
}

// Count arguments matching a predicate
template <typename Pred, typename... Args>
int count_if(Pred pred, Args... args) {
    return (... + (pred(args) ? 1 : 0));
}

// Find the minimum of all arguments
template <typename T, typename... Rest>
T min_of(T first, Rest... rest) {
    if constexpr (sizeof...(rest) == 0) {
        return first;
    } else {
        T rest_min = min_of(rest...);
        return first < rest_min ? first : rest_min;
    }
}
