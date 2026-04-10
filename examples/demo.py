# examples/bell_image.py
# Quick demo of pix4q — Edge detection pipeline
 
from pix4q.core import Pix4QCompiler
 
# ── English ──────────────────────────────────────────────────────────────────
program_en = [
    "load examples/sample.png",   # Load and NEQR-encode image
    "grayscale",                  # Convert to grayscale
    "edge",                       # Quantum edge detection (XOR of neighbors)
    "save examples/edges_en.png", # Save result
]
 
compiler = Pix4QCompiler(image_size=8)
compiler.compile(program_en)
result = compiler.run()
compiler.print_log()
 
print("\nCircuit info:")
print(f"  Qubits : {result['circuit'].num_qubits}")
print(f"  Gates  : {result['circuit'].size()}")
print(f"  Depth  : {result['circuit'].depth()}")
 
# ── Spanish ───────────────────────────────────────────────────────────────────
program_es = [
    "cargar examples/sample.png",
    "gris",
    "borde",
    "guardar examples/bordes_es.png",
]
 
compiler2 = Pix4QCompiler(image_size=8)
compiler2.compile(program_es)
result2 = compiler2.run()
compiler2.print_log()
 
# ── Full pipeline ─────────────────────────────────────────────────────────────
pipeline = [
    "load examples/sample.png",
    "grayscale",
    "threshold 100",
    "invert",
    "flip_h",
    "blur",
    "save examples/full_pipeline.png",
]
 
compiler3 = Pix4QCompiler(image_size=8)
compiler3.compile(pipeline)
result3 = compiler3.run()
compiler3.print_log()
