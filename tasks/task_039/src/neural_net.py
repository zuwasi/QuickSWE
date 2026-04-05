"""
Simple multi-layer perceptron (MLP) with forward and backward passes.

Supports dense layers with configurable activations (ReLU, sigmoid, tanh),
softmax output, and cross-entropy loss. All operations use pure Python
and basic math — no external ML frameworks.
"""

import math
import random
from typing import List, Optional, Tuple, Callable


def _zeros(rows: int, cols: int) -> List[List[float]]:
    return [[0.0] * cols for _ in range(rows)]


def _random_matrix(rows: int, cols: int, scale: float = 0.1) -> List[List[float]]:
    return [[random.gauss(0, scale) for _ in range(cols)] for _ in range(rows)]


def _matmul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    assert cols_a == rows_b
    result = _zeros(rows_a, cols_b)
    for i in range(rows_a):
        for k in range(cols_a):
            if a[i][k] == 0:
                continue
            for j in range(cols_b):
                result[i][j] += a[i][k] * b[k][j]
    return result


def _transpose(m: List[List[float]]) -> List[List[float]]:
    rows, cols = len(m), len(m[0])
    return [[m[i][j] for i in range(rows)] for j in range(cols)]


def _add_bias(m: List[List[float]], bias: List[float]) -> List[List[float]]:
    return [[m[i][j] + bias[j] for j in range(len(bias))] for i in range(len(m))]


def _elementwise(m: List[List[float]], fn: Callable[[float], float]) -> List[List[float]]:
    return [[fn(x) for x in row] for row in m]


def relu(x: float) -> float:
    return max(0.0, x)


def relu_derivative(x: float) -> float:
    return 1.0 if x > 0 else 0.0


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    else:
        ez = math.exp(x)
        return ez / (1.0 + ez)


def sigmoid_derivative(x: float) -> float:
    s = sigmoid(x)
    return s * (1.0 - s)


def tanh_fn(x: float) -> float:
    return math.tanh(x)


def tanh_derivative(x: float) -> float:
    t = math.tanh(x)
    return 1.0 - t * t


ACTIVATIONS = {
    "relu": (relu, relu_derivative),
    "sigmoid": (sigmoid, sigmoid_derivative),
    "tanh": (tanh_fn, tanh_derivative),
}


def softmax(logits: List[float]) -> List[float]:
    max_val = max(logits)
    exps = [math.exp(x - max_val) for x in logits]
    total = sum(exps)
    return [e / total for e in exps]


def cross_entropy_loss(probs: List[float], target: int) -> float:
    p = max(probs[target], 1e-15)
    return -math.log(p)


def softmax_cross_entropy_gradient(logits: List[float], target: int) -> List[float]:
    """
    Compute gradient of cross-entropy loss w.r.t. logits.
    
    The correct formula is: grad[i] = softmax(logits)[i] - (1 if i == target else 0)
    """
    probs = softmax(logits)
    grad = []
    for i in range(len(probs)):
        grad.append(probs[i] - 1)
    return grad


class DenseLayer:
    """Fully connected layer."""

    def __init__(self, input_size: int, output_size: int, activation: str = "relu"):
        self.input_size = input_size
        self.output_size = output_size
        self.activation_name = activation

        scale = math.sqrt(2.0 / input_size)
        self.weights = _random_matrix(input_size, output_size, scale)
        self.biases = [0.0] * output_size

        self.weight_grads = _zeros(input_size, output_size)
        self.bias_grads = [0.0] * output_size

        self._input_cache: Optional[List[List[float]]] = None
        self._pre_activation_cache: Optional[List[List[float]]] = None

        if activation in ACTIVATIONS:
            self._act_fn, self._act_deriv = ACTIVATIONS[activation]
        else:
            self._act_fn = None
            self._act_deriv = None

    def forward(self, x: List[List[float]]) -> List[List[float]]:
        self._input_cache = x
        z = _matmul(x, self.weights)
        z = _add_bias(z, self.biases)
        self._pre_activation_cache = z

        if self._act_fn:
            return _elementwise(z, self._act_fn)
        return z

    def backward(self, grad_output: List[List[float]], learning_rate: float) -> List[List[float]]:
        batch_size = len(grad_output)

        if self._act_deriv and self._pre_activation_cache:
            grad_activated = []
            for i in range(batch_size):
                row = []
                for j in range(self.output_size):
                    row.append(grad_output[i][j] * self._act_deriv(self._pre_activation_cache[i][j]))
                grad_activated.append(row)
        else:
            grad_activated = grad_output

        input_t = _transpose(self._input_cache)
        self.weight_grads = _matmul(input_t, grad_activated)

        self.bias_grads = [0.0] * self.output_size
        for i in range(batch_size):
            for j in range(self.output_size):
                self.bias_grads[j] += grad_activated[i][j]

        weights_t = _transpose(self.weights)
        grad_input = _matmul(grad_activated, weights_t)

        for i in range(self.input_size):
            for j in range(self.output_size):
                self.weights[i][j] -= learning_rate * self.weight_grads[i][j] / batch_size
        for j in range(self.output_size):
            self.biases[j] -= learning_rate * self.bias_grads[j] / batch_size

        return grad_input


class MLP:
    """Multi-layer perceptron."""

    def __init__(self, layer_sizes: List[int], activations: Optional[List[str]] = None):
        if activations is None:
            activations = ["relu"] * (len(layer_sizes) - 2) + ["none"]

        self.layers: List[DenseLayer] = []
        for i in range(len(layer_sizes) - 1):
            act = activations[i] if i < len(activations) else "relu"
            self.layers.append(DenseLayer(layer_sizes[i], layer_sizes[i + 1], act))

    def forward(self, x: List[List[float]]) -> List[List[float]]:
        out = x
        for layer in self.layers:
            out = layer.forward(out)
        return out

    def predict(self, x: List[float]) -> int:
        out = self.forward([x])
        logits = out[0]
        return logits.index(max(logits))

    def predict_probs(self, x: List[float]) -> List[float]:
        out = self.forward([x])
        return softmax(out[0])

    def train_step(self, x_batch: List[List[float]], y_batch: List[int],
                   learning_rate: float = 0.01) -> float:
        logits_batch = self.forward(x_batch)
        batch_size = len(x_batch)

        total_loss = 0.0
        grad_batch = []

        for i in range(batch_size):
            logits = logits_batch[i]
            target = y_batch[i]

            probs = softmax(logits)
            loss = cross_entropy_loss(probs, target)
            total_loss += loss

            grad = softmax_cross_entropy_gradient(logits, target)
            grad_batch.append(grad)

        for layer in reversed(self.layers):
            grad_batch = layer.backward(grad_batch, learning_rate)

        return total_loss / batch_size

    def train(self, x_data: List[List[float]], y_data: List[int],
              epochs: int = 100, learning_rate: float = 0.01,
              batch_size: int = 32) -> List[float]:
        losses = []
        n = len(x_data)

        for epoch in range(epochs):
            indices = list(range(n))
            random.shuffle(indices)
            epoch_loss = 0.0
            num_batches = 0

            for start in range(0, n, batch_size):
                end = min(start + batch_size, n)
                batch_indices = indices[start:end]
                x_batch = [x_data[i] for i in batch_indices]
                y_batch = [y_data[i] for i in batch_indices]

                loss = self.train_step(x_batch, y_batch, learning_rate)
                epoch_loss += loss
                num_batches += 1

            avg_loss = epoch_loss / num_batches
            losses.append(avg_loss)

        return losses


def generate_xor_data(n: int = 200) -> Tuple[List[List[float]], List[int]]:
    """Generate XOR-like classification data."""
    x_data = []
    y_data = []
    for _ in range(n):
        x1 = random.uniform(-1, 1)
        x2 = random.uniform(-1, 1)
        label = 1 if (x1 > 0) != (x2 > 0) else 0
        x_data.append([x1, x2])
        y_data.append(label)
    return x_data, y_data


def generate_spiral_data(n_per_class: int = 100, n_classes: int = 3
                         ) -> Tuple[List[List[float]], List[int]]:
    """Generate spiral classification data."""
    x_data = []
    y_data = []
    for c in range(n_classes):
        for i in range(n_per_class):
            r = i / n_per_class
            t = c * 4.0 + (i / n_per_class) * 4.0 + random.gauss(0, 0.2)
            x_data.append([r * math.cos(t), r * math.sin(t)])
            y_data.append(c)
    return x_data, y_data
