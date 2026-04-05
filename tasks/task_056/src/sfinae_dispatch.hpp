#pragma once
#include <string>
#include <type_traits>
#include <sstream>

// Trait: does T have a .serialize() method?
template <typename T, typename = void>
struct has_serialize : std::false_type {};

template <typename T>
struct has_serialize<T, std::void_t<decltype(std::declval<T>().serialize())>>
    : std::true_type {};

// Arithmetic dispatch
template <typename T>
typename std::enable_if<std::is_arithmetic<T>::value, std::string>::type
serialize(const T& val) {
    std::ostringstream oss;
    oss << "arithmetic:" << val;
    return oss.str();
}

// Custom .serialize() dispatch
template <typename T>
typename std::enable_if<has_serialize<T>::value && !std::is_arithmetic<T>::value,
                        std::string>::type
serialize(const T& val) {
    return "custom:" + val.serialize();
}

// Fallback
template <typename T>
typename std::enable_if<!has_serialize<T>::value && !std::is_arithmetic<T>::value,
                        std::string>::type
serialize(const T&) {
    return "fallback:unknown";
}

// Helper to classify
template <typename T>
std::string classify() {
    if constexpr (std::is_arithmetic<T>::value)
        return "arithmetic";
    else if constexpr (has_serialize<T>::value)
        return "custom";
    else
        return "fallback";
}
