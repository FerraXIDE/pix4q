# pix4q/encoder.py
# NEQR (Novel Enhanced Quantum Representation) image encoder
#
# A 2^n × 2^n grayscale image is encoded as:
#   |I> = 1/2^n * Σ |f(Y,X)>|Y>|X>
#
# Qubits layout:
#   [intensity_qubits (8)] + [row_qubits (n)] + [col_qubits (n)]

import math
import numpy as np
from PIL import Image
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


def load_image(path: str, size: int = 4) -> np.ndarray:
    """Load image, convert to grayscale, resize to size×size (must be power of 2)."""
    img = Image.open(path).convert("L")
    img = img.resize((size, size), Image.LANCZOS)
    return np.array(img, dtype=np.uint8)


def image_from_array(arr: np.ndarray) -> np.ndarray:
    """Normalize any 2D array to uint8 grayscale."""
    arr = np.array(arr, dtype=float)
    if arr.max() > arr.min():
        arr = (arr - arr.min()) / (arr.max() - arr.min()) * 255
    return arr.astype(np.uint8)


def encode_neqr(pixels: np.ndarray) -> QuantumCircuit:
    """
    Encode a 2^n × 2^n grayscale image into a NEQR quantum circuit.

    For a size × size image:
      - n = log2(size) qubits for rows
      - n = log2(size) qubits for cols
      - 8 qubits for intensity (grayscale 0-255)

    Total qubits: 2n + 8
    """
    size = pixels.shape[0]
    assert size == pixels.shape[1], "Image must be square"
    assert (size & (size - 1)) == 0, "Image size must be a power of 2"

    n = int(math.log2(size))           # qubits per dimension
    intensity_bits = 8                 # 0-255 grayscale
    total_qubits = intensity_bits + 2 * n

    # Registers
    intensity = QuantumRegister(intensity_bits, name='i')
    row       = QuantumRegister(n, name='y')
    col       = QuantumRegister(n, name='x')
    qc        = QuantumCircuit(intensity, row, col)

    # Step 1: Hadamard on all position qubits → superposition of all pixel addresses
    for q in row:
        qc.h(q)
    for q in col:
        qc.h(q)

    # Step 2: For each pixel, encode intensity using controlled-X gates
    # We use multi-controlled X (mcx) on intensity qubits conditioned on position
    for y in range(size):
        for x in range(size):
            pixel_val = int(pixels[y, x])
            if pixel_val == 0:
                continue  # |00000000> is already the default

            # Encode row address y into row register (flip 0-bits temporarily)
            row_bits  = format(y, f'0{n}b')
            col_bits  = format(x, f'0{n}b')

            # Add X gates to flip 0-bits so controls fire on this specific address
            for bit_idx, bit in enumerate(row_bits):
                if bit == '0':
                    qc.x(row[bit_idx])
            for bit_idx, bit in enumerate(col_bits):
                if bit == '0':
                    qc.x(col[bit_idx])

            # For each '1' bit in the pixel intensity, apply mcx
            intensity_bits_str = format(pixel_val, '08b')
            control_qubits = list(row) + list(col)
            for bit_idx, bit in enumerate(intensity_bits_str):
                if bit == '1':
                    qc.mcx(control_qubits, intensity[bit_idx])

            # Undo the X flips
            for bit_idx, bit in enumerate(row_bits):
                if bit == '0':
                    qc.x(row[bit_idx])
            for bit_idx, bit in enumerate(col_bits):
                if bit == '0':
                    qc.x(col[bit_idx])

    return qc


def decode_statevector(statevector: np.ndarray, size: int) -> np.ndarray:
    """
    Reconstruct a pixel array from a NEQR statevector.

    The statevector has 2^(8 + 2n) amplitudes.
    Each basis state encodes: |intensity(8 bits)>|row(n bits)>|col(n bits)>
    """
    n = int(math.log2(size))
    pixels = np.zeros((size, size), dtype=np.float64)
    norm   = np.zeros((size, size), dtype=np.float64)

    total_qubits = 8 + 2 * n
    num_states   = 2 ** total_qubits

    for state_idx in range(num_states):
        amplitude = statevector[state_idx]
        prob      = abs(amplitude) ** 2
        if prob < 1e-10:
            continue

        # Qiskit bit ordering: least significant bit is qubit 0 (col[0])
        bits = format(state_idx, f'0{total_qubits}b')
        # bits layout (MSB to LSB): intensity(8) | row(n) | col(n)
        # But Qiskit statevector index has qubit 0 as LSB
        # So we reverse:
        bits_le = bits[::-1]  # little-endian: bit 0 = col[0], ... , bit 2n+7 = i[7]

        col_bits       = bits_le[0:n]
        row_bits       = bits_le[n:2*n]
        intensity_bits = bits_le[2*n:2*n+8]

        col_val       = int(col_bits[::-1], 2)
        row_val       = int(row_bits[::-1], 2)
        intensity_val = int(intensity_bits[::-1], 2)

        if 0 <= row_val < size and 0 <= col_val < size:
            pixels[row_val, col_val] += prob * intensity_val
            norm[row_val, col_val]   += prob

    # Normalize
    mask = norm > 1e-10
    pixels[mask] = pixels[mask] / norm[mask]

    return np.clip(pixels, 0, 255).astype(np.uint8)


def decode_counts(counts: dict, size: int, shots: int) -> np.ndarray:
    """
    Reconstruct pixel array from measurement counts.
    Each measurement result is a bitstring: intensity|row|col
    """
    n      = int(math.log2(size))
    pixels = np.zeros((size, size), dtype=np.float64)
    hits   = np.zeros((size, size), dtype=np.float64)

    for bitstring, count in counts.items():
        # Qiskit returns bitstring MSB first, spaces between registers removed
        clean = bitstring.replace(' ', '')
        total_bits = 8 + 2 * n
        if len(clean) < total_bits:
            clean = clean.zfill(total_bits)

        # Split: intensity (8 bits) | row (n) | col (n)  — MSB first
        intensity_str = clean[0:8]
        row_str       = clean[8:8+n]
        col_str       = clean[8+n:8+2*n]

        intensity_val = int(intensity_str, 2)
        row_val       = int(row_str, 2)
        col_val       = int(col_str, 2)

        if 0 <= row_val < size and 0 <= col_val < size:
            pixels[row_val, col_val] += intensity_val * count
            hits[row_val, col_val]   += count

    mask = hits > 0
    pixels[mask] = pixels[mask] / hits[mask]

    return np.clip(pixels, 0, 255).astype(np.uint8)
