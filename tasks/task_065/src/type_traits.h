#ifndef MY_TYPE_TRAITS_H
#define MY_TYPE_TRAITS_H

/* --- my_is_same --- */
template<typename T, typename U>
struct my_is_same {
    static constexpr bool value = false;
};

template<typename T>
struct my_is_same<T, T> {
    static constexpr bool value = true;
};

/* --- my_is_pointer --- */
template<typename T>
struct my_is_pointer {
    static constexpr bool value = false;
};

template<typename T>
struct my_is_pointer<T*> {
    static constexpr bool value = true;
};

/*
 * BUG: missing specializations for cv-qualified pointer types:
 *   int* const       -> T* matches, but const-qualified T* doesn't
 *   int* volatile    -> same issue
 *   int* const volatile -> same issue
 *
 * The partial specialization T* only matches plain pointers.
 * For const-qualified pointers (e.g., int* const), the type is
 * "const pointer to int", and T* doesn't match "T* const".
 */

/* --- my_is_const --- */
template<typename T>
struct my_is_const {
    static constexpr bool value = false;
};

template<typename T>
struct my_is_const<const T> {
    static constexpr bool value = true;
};

/* --- my_remove_const --- */
template<typename T>
struct my_remove_const {
    using type = T;
};

template<typename T>
struct my_remove_const<const T> {
    using type = T;
};

/* Note: const volatile T is handled by the const T specialization
 * where T = volatile U, yielding type = volatile U. This works correctly. */

/* --- my_remove_pointer --- */
template<typename T>
struct my_remove_pointer {
    using type = T;
};

template<typename T>
struct my_remove_pointer<T*> {
    using type = T;
};

/*
 * BUG: my_remove_pointer doesn't handle const/volatile qualified pointers
 * e.g., my_remove_pointer<int* const>::type should be int, but it remains int* const
 */

#endif
