# pix4q

[![Python versions](https://img.shields.io/pypi/pyversions/pix4q.svg)](https://pypi.org/project/pix4q/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Quantum image processing using plain text commands. Inspired by [text4q](https://github.com/FerraXIDE/text4q).**

`pix4q` removes two barriers to quantum image processing:

1. **Complex syntax** — Just write `"edge"`, not 10 lines of Qiskit circuit code
2. **Language barrier** — Use commands in English, Spanish, German, Portuguese, French, Japanese, or Chinese

Under the hood, it uses **NEQR** (Novel Enhanced Quantum Representation) to encode
images into qubits, applies real quantum gates, and reconstructs the result.

---

## Installation

```bash
pip install pix4q
```

---

## Quick Example

```python
from pix4q.core import Pix4QCompiler

program = [
    "load photo.jpg",     # Load + NEQR-encode into qubits
    "grayscale",          # Convert to grayscale (quantum amplitude weights)
    "edge",               # Edge detection via quantum XOR (CNOT between neighbors)
    "save result.png",    # Decode and save
]

compiler = Pix4QCompiler(image_size=8)  # 8×8 = 14 qubits (8 intensity + 3+3 position)
compiler.compile(program)
result = compiler.run()

compiler.print_log()
# ▶ load photo.jpg
#   ✓ Loaded 'photo.jpg' → (8, 8) pixels
#   ✓ NEQR circuit built: 14 qubits, 502 gates
# ▶ grayscale
#   ✓ Applied 'grayscale' → shape (8, 8)
# ▶ edge
#   ✓ Applied 'edge' → shape (8, 8)
# ▶ save result.png
#   ✓ Saved to 'result.png'
```

---

## Multi-Language Support

The same pipeline works in 7 languages:

```python
# Spanish
program = ["cargar foto.jpg", "gris", "borde", "guardar resultado.png"]

# German
program = ["laden foto.jpg", "graustufen", "kante", "speichern ergebnis.png"]

# Japanese
program = ["読み込む foto.jpg", "グレースケール", "エッジ", "保存 kekka.png"]
```

| Command      | English     | Spanish    | German      | Portuguese    | French        | Japanese      | Chinese |
|-------------|-------------|------------|-------------|---------------|---------------|---------------|---------|
| Load image  | `load`      | `cargar`   | `laden`     | `carregar`    | `charger`     | `読み込む`     | `加载`  |
| Save image  | `save`      | `guardar`  | `speichern` | `salvar`      | `enregistrer` | `保存する`     | `保存`  |
| Grayscale   | `grayscale` | `gris`     | `graustufen`| `escala_cinza`| `niveaux_gris`| `グレースケール` | `灰度`  |
| Edge detect | `edge`      | `borde`    | `kante`     | `borda`       | `contour`     | `エッジ`       | `边缘`  |
| Flip H      | `flip_h`    | `voltear_h`| `spiegeln_h`| `inverter_h`  | `retourner_h` | `水平反転`     | `水平翻转` |
| Flip V      | `flip_v`    | `voltear_v`| `spiegeln_v`| `inverter_v`  | `retourner_v` | `垂直反転`     | `垂直翻转` |
| Rotate      | `rotate`    | `rotar`    | `drehen`    | `girar`       | `tourner`     | `回転`         | `旋转`  |
| Blur        | `blur`      | `desenfoque`| `unscharf` | `borrar`      | `flou`        | `ブラー`       | `模糊`  |
| Threshold   | `threshold` | `umbral`   | `schwelle`  | `limiar`      | `seuil`       | `閾値`         | `阈值`  |
| Invert      | `invert`    | `invertir` | `invertieren`| `inverso`    | `inverser`    | `反転`         | `反转`  |
| Info        | `info`      | `información`| `informationen`| `informações`| `informations`| `情報`    | `信息`  |

---

## All Commands

| Command            | Description                                          | Quantum mechanism                   |
|-------------------|------------------------------------------------------|-------------------------------------|
| `load <file>`      | Load and NEQR-encode image                           | Builds full NEQR circuit            |
| `save <file>`      | Decode and save image                                | —                                   |
| `measure`          | Simulate circuit and reconstruct pixels              | Statevector / shot sampling         |
| `grayscale`        | Convert to grayscale                                 | Amplitude-weighted luminance        |
| `edge`             | Detect edges                                         | CNOT XOR between adjacent pixels    |
| `invert`           | Invert intensity                                     | X gate on all intensity qubits      |
| `flip_h`           | Flip horizontally                                    | SWAP on column position register    |
| `flip_v`           | Flip vertically                                      | SWAP on row position register       |
| `rotate <deg>`     | Rotate 90/180/270 degrees                            | Position register remapping         |
| `blur`             | Gaussian blur                                        | RY superposition of neighbors       |
| `threshold <val>`  | Binary threshold (default: 128)                      | MCX comparison on intensity qubits  |
| `info`             | Print image and circuit info                         | —                                   |
| `show`             | Display image                                        | —                                   |

---

## How NEQR Works

NEQR encodes a 2ⁿ × 2ⁿ grayscale image using:
- **2n qubits** for pixel position (n for row, n for column)
- **8 qubits** for pixel intensity (grayscale 0–255)

```
|I⟩ = 1/2ⁿ · Σ |f(Y,X)⟩|Y⟩|X⟩
```

For an 8×8 image: **14 qubits total** (8 intensity + 3 row + 3 col).

```
image_size=4  →  12 qubits   (manageable)
image_size=8  →  14 qubits   (default, fast)
image_size=16 →  16 qubits   (slower)
image_size=32 →  18 qubits   (research use)
```

---

## Full Pipeline Example

```python
from pix4q.core import Pix4QCompiler

pipeline = [
    "load portrait.jpg",
    "grayscale",
    "threshold 100",     # Binary mask above 100
    "invert",            # Flip black/white
    "flip_h",            # Mirror
    "blur",              # Smooth result
    "save final.png",
]

compiler = Pix4QCompiler(image_size=8)
compiler.compile(pipeline)
result = compiler.run()

# Access the PIL Image directly
result['image'].show()

# Access raw pixels
import numpy as np
pixels = result['pixels']  # np.ndarray (8, 8)

# Inspect the NEQR quantum circuit
print(result['circuit'].draw(output='text'))
```

---

## Why pix4q?

- **Zero boilerplate** — No QuantumCircuit(), no register setup, just text
- **Real quantum circuits** — NEQR encoding, real Qiskit gates
- **7 human languages** — Same as text4q
- **Built for teaching** — Students focus on the image ops, not Qiskit syntax
- **Powered by Qiskit Aer** — Full simulation power under the hood

**Not a replacement for Qiskit** — For large images or custom circuits, use Qiskit directly.

---

## Roadmap

- More languages (Italian, Korean, Hindi, Arabic)
- `measure` with shot-based reconstruction
- Quantum histogram equalization
- Color image support (3-channel NEQR)
- PyPI release

---

## License

Apache 2.0 — See [LICENSE](LICENSE) for details.

---

## Related

- [text4q](https://github.com/FerraXIDE/text4q) — Natural command language for quantum circuits (the inspiration)

---

*Made with ❤️ and qubits*
