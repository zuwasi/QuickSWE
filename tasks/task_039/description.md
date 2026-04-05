# Task 039: Neural Network Backpropagation Gradient Bug

## Description

A simple MLP (multi-layer perceptron) implementation with forward and backward passes
has a bug in the combined softmax + cross-entropy loss gradient computation. The backward
pass computes the gradient of the softmax-cross-entropy loss incorrectly.

## Bug

The correct gradient of cross-entropy loss with respect to the logits (pre-softmax)
is `softmax_output - one_hot_target`, i.e., subtract 1 only from the position
corresponding to the true class. The buggy implementation subtracts 1 from ALL
positions of the softmax output, which produces entirely wrong gradients.

## Expected Behavior

The gradient should be `softmax(z) - one_hot(y)` where only position `y` has 1
subtracted from it. This ensures proper gradient descent on the parameters.
