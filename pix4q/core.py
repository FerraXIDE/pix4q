# pix4q/core.py
# Pix4QCompiler — main entry point
# Philosophy: same as text4q — a list of strings, zero boilerplate.

import math
import numpy as np
from PIL import Image

from .languages  import resolve
from .encoder    import load_image, encode_neqr, decode_statevector, image_from_array
from .operations import apply_operation


class Pix4QCompiler:
    """
    Compile and run quantum image processing programs.

    Usage:
        compiler = Pix4QCompiler()
        compiler.compile([
            "load photo.jpg",
            "grayscale",
            "edge",
            "save result.png"
        ])
        result = compiler.run()

    Multi-language example (Spanish):
        compiler.compile([
            "cargar foto.jpg",
            "gris",
            "borde",
            "guardar resultado.png"
        ])
    """

    # Operations that transform pixels (no arguments or with arguments)
    _PIXEL_OPS = {"grayscale", "invert", "flip_h", "flip_v",
                  "rotate", "threshold", "edge", "blur"}

    def __init__(self, image_size: int = 8):
        """
        Args:
            image_size: Target size for NEQR encoding (must be power of 2).
                        4 → 4×4, 8 → 8×8 (default), 16 → 16×16.
                        Larger sizes = more qubits = slower simulation.
        """
        assert (image_size & (image_size - 1)) == 0, "image_size must be power of 2"
        self.image_size  = image_size
        self._program    = []
        self._pixels     = None    # current working pixel array (np.ndarray)
        self._save_path  = None
        self._circuit    = None    # last NEQR circuit built
        self._log        = []      # execution log

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def compile(self, program: list[str]) -> "Pix4QCompiler":
        """Parse and validate a list of text commands."""
        self._program = []
        for line_raw in program:
            line = line_raw.strip()
            if not line or line.startswith("#"):
                continue
            parts   = line.split()
            cmd_raw = parts[0]
            args    = parts[1:]
            cmd     = resolve(cmd_raw)
            self._program.append((cmd, args, line_raw))

        self._validate()
        return self

    def run(self, shots: int = 1024, use_statevector: bool = True) -> dict:
        """
        Execute the compiled program.

        Args:
            shots:            Number of measurement shots (used if use_statevector=False).
            use_statevector:  If True, use statevector simulation (exact, slower for
                              large images). If False, use shot-based sampling.

        Returns:
            dict with keys:
                'pixels'   — final np.ndarray image
                'image'    — PIL Image object
                'circuit'  — last NEQR QuantumCircuit built
                'log'      — list of execution steps
        """
        self._log = []

        for cmd, args, raw in self._program:
            self._log.append(f"▶ {raw}")

            if cmd == "load":
                self._handle_load(args)

            elif cmd == "save":
                self._handle_save(args)

            elif cmd == "measure":
                self._handle_measure(shots, use_statevector)

            elif cmd == "info":
                self._handle_info()

            elif cmd == "show":
                self._handle_show()

            elif cmd in self._PIXEL_OPS:
                self._ensure_pixels()
                self._pixels = apply_operation(self._pixels, cmd, args)
                self._log.append(f"  ✓ Applied '{cmd}' → shape {self._pixels.shape}")

            else:
                raise ValueError(f"[pix4q] Unknown command: '{cmd}' (from '{raw}')")

        return {
            "pixels":  self._pixels,
            "image":   Image.fromarray(self._pixels) if self._pixels is not None else None,
            "circuit": self._circuit,
            "log":     self._log,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Convenience properties
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def pixels(self) -> np.ndarray:
        return self._pixels

    @property
    def image(self):
        if self._pixels is None:
            return None
        return Image.fromarray(self._pixels)

    @property
    def circuit(self):
        return self._circuit

    # ──────────────────────────────────────────────────────────────────────────
    # Internal handlers
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_load(self, args: list):
        if not args:
            raise ValueError("[pix4q] 'load' requires a file path. Example: 'load image.png'")
        path = args[0]
        self._pixels = load_image(path, size=self.image_size)
        self._log.append(f"  ✓ Loaded '{path}' → {self._pixels.shape} pixels")

        # Build NEQR circuit (but don't simulate yet — wait for 'measure')
        self._circuit = encode_neqr(self._pixels)
        n_qubits = self._circuit.num_qubits
        self._log.append(f"  ✓ NEQR circuit built: {n_qubits} qubits, "
                         f"{len(self._circuit)} gates")

    def _handle_save(self, args: list):
        if not args:
            raise ValueError("[pix4q] 'save' requires a file path. Example: 'save result.png'")
        self._ensure_pixels()
        path = args[0]
        img = Image.fromarray(self._pixels)
        img.save(path)
        self._log.append(f"  ✓ Saved to '{path}'")

    def _handle_measure(self, shots: int, use_statevector: bool):
        """
        Build NEQR circuit from current pixels and simulate it.
        Updates self._pixels with the reconstructed image.
        """
        self._ensure_pixels()
        size = self.image_size

        # Re-encode current (possibly transformed) pixel state
        self._circuit = encode_neqr(self._pixels)

        if use_statevector:
            self._log.append(f"  ⚛  Running statevector simulation "
                             f"({self._circuit.num_qubits} qubits)...")
            from qiskit_aer import AerSimulator
            from qiskit import transpile
            qc_sv = self._circuit.copy()
            qc_sv.save_statevector()
            sim    = AerSimulator(method='statevector')
            tqc    = transpile(qc_sv, sim)
            result = sim.run(tqc).result()
            sv     = np.array(result.get_statevector())
            self._pixels = decode_statevector(sv, size)
        else:
            self._log.append(f"  ⚛  Running shot-based simulation "
                             f"({shots} shots, {self._circuit.num_qubits} qubits)...")
            from qiskit_aer import AerSimulator
            from qiskit import transpile, ClassicalRegister
            from .encoder import decode_counts
            qc_m = self._circuit.copy()
            cr   = ClassicalRegister(self._circuit.num_qubits, 'c')
            qc_m.add_register(cr)
            qc_m.measure_all()
            sim    = AerSimulator()
            tqc    = transpile(qc_m, sim)
            result = sim.run(tqc, shots=shots).result()
            counts = result.get_counts()
            self._pixels = decode_counts(counts, size, shots)

        self._log.append(f"  ✓ Measured → reconstructed {size}×{size} image")

    def _handle_info(self):
        if self._pixels is None:
            self._log.append("  ℹ  No image loaded yet.")
            return
        size    = self._pixels.shape[0]
        n       = int(math.log2(size))
        qubits  = 8 + 2 * n
        self._log.append(
            f"  ℹ  Image: {self._pixels.shape} | "
            f"NEQR qubits: {qubits} (8 intensity + {n}+{n} position) | "
            f"Min: {self._pixels.min()} Max: {self._pixels.max()}"
        )

    def _handle_show(self):
        if self._pixels is None:
            self._log.append("  ℹ  No image to show.")
            return
        img = Image.fromarray(self._pixels)
        img.show()
        self._log.append(f"  ✓ Displayed image ({self._pixels.shape})")

    def _ensure_pixels(self):
        if self._pixels is None:
            raise RuntimeError(
                "[pix4q] No image loaded. Use 'load <file>' first."
            )

    def _validate(self):
        """Basic validation before running."""
        cmds = [cmd for cmd, _, _ in self._program]
        if not cmds:
            raise ValueError("[pix4q] Empty program.")

    # ──────────────────────────────────────────────────────────────────────────
    # Display helpers
    # ──────────────────────────────────────────────────────────────────────────

    def print_log(self):
        """Print the execution log."""
        print("\n".join(self._log))

    def print_circuit(self):
        """Print the NEQR circuit diagram."""
        if self._circuit is None:
            print("[pix4q] No circuit built yet. Run compile() + run() first.")
            return
        print(self._circuit.draw(output='text'))
