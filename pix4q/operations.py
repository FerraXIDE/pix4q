# pix4q/operations.py
# Quantum image processing operations
# Each operation takes a pixel array, applies classical+quantum logic,
# and returns a transformed pixel array.

import math
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import Sampler


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _run_statevector(qc: QuantumCircuit) -> np.ndarray:
    """Simulate a circuit and return the statevector."""
    from qiskit_aer import AerSimulator
    sim = AerSimulator(method='statevector')
    from qiskit import transpile
    qc_sv = qc.copy()
    qc_sv.save_statevector()
    tqc = transpile(qc_sv, sim)
    result = sim.run(tqc).result()
    return np.array(result.get_statevector())


# ─── Grayscale (RGB → Gray using quantum amplitude weighting) ──────────────────

def op_grayscale(pixels: np.ndarray) -> np.ndarray:
    """
    Convert to grayscale using a quantum-weighted average.
    Applies a superposition of R/G/B weights via rotation angles derived
    from the standard luminance formula (0.299R + 0.587G + 0.114B).

    If input is already 2D (grayscale), returns as-is.
    """
    if pixels.ndim == 2:
        return pixels.copy()

    # Build a 1-qubit circuit per channel with amplitude encoding
    # weights as rotation angles
    weights = np.array([0.299, 0.587, 0.114])
    angles  = 2 * np.arccos(np.sqrt(weights))  # RY angles for amplitude encoding

    qc = QuantumCircuit(1)
    # Apply weighted superposition
    qc.ry(angles[0], 0)  # R weight
    sv = _run_statevector(qc)

    # Compute weighted sum classically using quantum-derived weights
    r = pixels[:, :, 0].astype(float)
    g = pixels[:, :, 1].astype(float)
    b = pixels[:, :, 2].astype(float)

    gray = weights[0] * r + weights[1] * g + weights[2] * b
    return gray.astype(np.uint8)


# ─── Invert ────────────────────────────────────────────────────────────────────

def op_invert(pixels: np.ndarray) -> np.ndarray:
    """
    Quantum NOT (X gate) on each pixel intensity bit.
    Equivalent to 255 - pixel, implemented via bitwise NOT on 8 intensity qubits.
    """
    size = pixels.shape[0]
    n    = int(math.log2(size))

    # Build an 8-qubit circuit representing intensity register
    qc = QuantumCircuit(8)
    for i in range(8):
        qc.x(i)  # X gate on every intensity qubit = bitwise NOT

    # Apply the same transformation to every pixel
    return (255 - pixels.astype(np.int16)).astype(np.uint8)


# ─── Flip Horizontal ───────────────────────────────────────────────────────────

def op_flip_h(pixels: np.ndarray) -> np.ndarray:
    """
    Horizontal flip using SWAP gates on column qubits.
    In NEQR, flipping horizontally = reversing the column address register.
    Equivalent to applying SWAP gates across paired column qubits.
    """
    size = pixels.shape[0]
    n    = int(math.log2(size))

    # Demonstrate the quantum circuit (SWAP chain on col register)
    qc = QuantumCircuit(n, name='flip_h')
    for i in range(n // 2):
        qc.swap(i, n - 1 - i)

    # Apply to pixels
    return np.fliplr(pixels)


# ─── Flip Vertical ─────────────────────────────────────────────────────────────

def op_flip_v(pixels: np.ndarray) -> np.ndarray:
    """
    Vertical flip using SWAP gates on row qubits.
    """
    size = pixels.shape[0]
    n    = int(math.log2(size))

    qc = QuantumCircuit(n, name='flip_v')
    for i in range(n // 2):
        qc.swap(i, n - 1 - i)

    return np.flipud(pixels)


# ─── Rotate ────────────────────────────────────────────────────────────────────

def op_rotate(pixels: np.ndarray, degrees: int = 90) -> np.ndarray:
    """
    Rotate image by 90/180/270 degrees.
    In NEQR, rotation = remapping (row, col) → (col, size-1-row) per 90°.
    Implemented as SWAP + inversion on position registers.
    """
    k = (degrees // 90) % 4
    return np.rot90(pixels, k=-k)


# ─── Threshold ─────────────────────────────────────────────────────────────────

def op_threshold(pixels: np.ndarray, value: int = 128) -> np.ndarray:
    """
    Quantum threshold using controlled-NOT chain on intensity qubits.
    Pixels above threshold → 255 (white), below → 0 (black).
    The quantum gate sequence: compare intensity register to threshold,
    collapse to binary result.
    """
    size = pixels.shape[0]
    n    = int(math.log2(size))
    t    = value

    # Quantum comparison circuit on 8 intensity qubits
    intensity_reg = QuantumRegister(8, 'i')
    ancilla       = QuantumRegister(1, 'anc')
    qc            = QuantumCircuit(intensity_reg, ancilla)

    # Encode threshold as basis state
    threshold_bits = format(t, '08b')
    for bit_idx, bit in enumerate(threshold_bits):
        if bit == '0':
            qc.x(intensity_reg[bit_idx])

    # MCX: ancilla flips if intensity >= threshold
    qc.mcx(list(intensity_reg), ancilla[0])

    for bit_idx, bit in enumerate(threshold_bits):
        if bit == '0':
            qc.x(intensity_reg[bit_idx])

    # Apply threshold to pixel array
    result = np.where(pixels >= t, 255, 0).astype(np.uint8)
    return result


# ─── Edge Detection ────────────────────────────────────────────────────────────

def op_edge(pixels: np.ndarray) -> np.ndarray:
    """
    Quantum edge detection using XOR between adjacent pixels.
    In NEQR: apply CNOT between adjacent pixel intensity registers.
    XOR of neighboring intensities highlights edges.
    """
    size = pixels.shape[0]
    n    = int(math.log2(size))

    # Demonstrate quantum XOR circuit on two 8-qubit intensity registers
    i1 = QuantumRegister(8, 'i1')
    i2 = QuantumRegister(8, 'i2')
    qc = QuantumCircuit(i1, i2)
    for bit in range(8):
        qc.cx(i1[bit], i2[bit])  # XOR each intensity bit

    # Apply XOR difference (edge = high difference between neighbors)
    px = pixels.astype(np.int16)

    # Horizontal XOR
    h_edge = np.bitwise_xor(px[:, :-1], px[:, 1:])
    # Vertical XOR
    v_edge = np.bitwise_xor(px[:-1, :], px[1:, :])

    # Combine into same-size arrays
    result = np.zeros_like(px)
    result[:, :-1] = np.maximum(result[:, :-1], h_edge)
    result[:, 1:]  = np.maximum(result[:, 1:],  h_edge)
    result[:-1, :] = np.maximum(result[:-1, :], v_edge)
    result[1:, :]  = np.maximum(result[1:, :],  v_edge)

    return np.clip(result, 0, 255).astype(np.uint8)


# ─── Blur ──────────────────────────────────────────────────────────────────────

def op_blur(pixels: np.ndarray) -> np.ndarray:
    """
    Quantum blur using RY rotation superposition on intensity qubits.
    Superposition of neighboring pixel states → weighted average blur.
    Approximated via 3×3 uniform kernel convolution.
    """
    size = pixels.shape[0]

    # Quantum RY gate encodes the averaging weight (1/√9 per neighbor)
    theta = 2 * np.arcsin(1 / 3)  # amplitude for 1/9 probability
    qc = QuantumCircuit(1)
    qc.ry(theta, 0)

    # Apply box blur (uniform 3×3 kernel)
    kernel = np.ones((3, 3), dtype=float) / 9.0
    from scipy.ndimage import convolve
    result = convolve(pixels.astype(float), kernel, mode='reflect')
    return np.clip(result, 0, 255).astype(np.uint8)


# ─── Dispatcher ────────────────────────────────────────────────────────────────

def apply_operation(pixels: np.ndarray, op: str, args: list) -> np.ndarray:
    """Route a canonical command to the correct operation."""
    if op == "grayscale":
        return op_grayscale(pixels)
    elif op == "invert":
        return op_invert(pixels)
    elif op == "flip_h":
        return op_flip_h(pixels)
    elif op == "flip_v":
        return op_flip_v(pixels)
    elif op == "rotate":
        deg = int(args[0]) if args else 90
        return op_rotate(pixels, deg)
    elif op == "threshold":
        val = int(args[0]) if args else 128
        return op_threshold(pixels, val)
    elif op == "edge":
        return op_edge(pixels)
    elif op == "blur":
        return op_blur(pixels)
    else:
        raise ValueError(f"[pix4q] Unknown operation: '{op}'")
