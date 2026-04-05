import os
import sys
import pytest
import math
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.neural_net import (
    softmax, cross_entropy_loss, softmax_cross_entropy_gradient,
    MLP, DenseLayer, relu, sigmoid, generate_xor_data,
)


class TestBasicComponents:
    """Tests that should pass both before and after the fix."""

    @pytest.mark.pass_to_pass
    def test_softmax_sums_to_one(self):
        logits = [2.0, 1.0, 0.1]
        probs = softmax(logits)
        assert abs(sum(probs) - 1.0) < 1e-10

    @pytest.mark.pass_to_pass
    def test_softmax_max_element(self):
        logits = [1.0, 5.0, 2.0]
        probs = softmax(logits)
        assert probs[1] > probs[0]
        assert probs[1] > probs[2]

    @pytest.mark.pass_to_pass
    def test_cross_entropy_loss_perfect(self):
        probs = [0.0, 1.0, 0.0]
        loss = cross_entropy_loss(probs, 1)
        assert abs(loss) < 1e-10


class TestGradients:
    """Tests that should fail before the fix and pass after."""

    @pytest.mark.fail_to_pass
    def test_gradient_full_vector(self):
        """Full gradient vector should be softmax(z) - one_hot(target)."""
        logits = [2.0, 1.0, 0.1]
        target = 0
        grad = softmax_cross_entropy_gradient(logits, target)
        probs = softmax(logits)
        expected = [probs[i] - (1.0 if i == target else 0.0) for i in range(len(logits))]
        for i in range(len(logits)):
            assert abs(grad[i] - expected[i]) < 1e-10, (
                f"Gradient[{i}]: got {grad[i]}, expected {expected[i]}. "
                f"Full grad={grad}, expected={expected}"
            )

    @pytest.mark.fail_to_pass
    def test_gradient_non_target_is_positive(self):
        """Gradient for non-target classes should equal softmax output (positive)."""
        logits = [2.0, 1.0, 0.1]
        target = 0
        grad = softmax_cross_entropy_gradient(logits, target)
        probs = softmax(logits)
        for i in range(len(logits)):
            if i != target:
                assert abs(grad[i] - probs[i]) < 1e-10, (
                    f"Gradient for class {i}: got {grad[i]}, expected {probs[i]}"
                )

    @pytest.mark.fail_to_pass
    def test_gradient_sums_to_zero(self):
        """Softmax-CE gradient should sum to zero."""
        logits = [1.5, -0.5, 2.0, 0.0]
        target = 2
        grad = softmax_cross_entropy_gradient(logits, target)
        grad_sum = sum(grad)
        assert abs(grad_sum) < 1e-10, (
            f"Gradient sum should be 0, got {grad_sum}"
        )

    @pytest.mark.fail_to_pass
    def test_mlp_loss_decreases_with_training(self):
        """MLP should learn XOR with correct gradients."""
        random.seed(42)
        x_data, y_data = generate_xor_data(200)

        mlp = MLP([2, 16, 2], activations=["relu", "none"])
        losses = mlp.train(x_data, y_data, epochs=100, learning_rate=0.1, batch_size=32)

        assert losses[-1] < losses[0] * 0.5, (
            f"Loss should decrease significantly: first={losses[0]:.4f}, last={losses[-1]:.4f}"
        )
