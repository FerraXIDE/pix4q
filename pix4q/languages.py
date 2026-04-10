# pix4q/languages.py
# Multi-language command aliases — same philosophy as text4q

ALIASES = {
    # LOAD
    "load":         "load",
    "cargar":       "load",   # Spanish
    "laden":        "load",   # German
    "carregar":     "load",   # Portuguese
    "charger":      "load",   # French
    "読み込む":      "load",   # Japanese
    "加载":          "load",   # Chinese

    # SAVE
    "save":         "save",
    "guardar":      "save",
    "speichern":    "save",
    "salvar":       "save",
    "enregistrer":  "save",
    "保存":          "save",
    "保存する":      "save",

    # MEASURE
    "measure":      "measure",
    "medir":        "measure",
    "messen":       "measure",
    "mesurer":      "measure",
    "測定":          "measure",
    "测量":          "measure",

    # GRAYSCALE
    "grayscale":    "grayscale",
    "gris":         "grayscale",
    "graustufen":   "grayscale",
    "escala_cinza": "grayscale",
    "niveaux_gris": "grayscale",
    "グレースケール": "grayscale",
    "灰度":          "grayscale",

    # EDGE DETECT
    "edge":         "edge",
    "borde":        "edge",
    "kante":        "edge",
    "borda":        "edge",
    "contour":      "edge",
    "エッジ":        "edge",
    "边缘":          "edge",

    # FLIP HORIZONTAL
    "flip_h":           "flip_h",
    "voltear_h":        "flip_h",
    "spiegeln_h":       "flip_h",
    "inverter_h":       "flip_h",
    "retourner_h":      "flip_h",
    "水平反転":           "flip_h",
    "水平翻转":           "flip_h",

    # FLIP VERTICAL
    "flip_v":           "flip_v",
    "voltear_v":        "flip_v",
    "spiegeln_v":       "flip_v",
    "inverter_v":       "flip_v",
    "retourner_v":      "flip_v",
    "垂直反転":           "flip_v",
    "垂直翻转":           "flip_v",

    # ROTATE
    "rotate":       "rotate",
    "rotar":        "rotate",
    "drehen":       "rotate",
    "girar":        "rotate",
    "tourner":      "rotate",
    "回転":          "rotate",
    "旋转":          "rotate",

    # BLUR
    "blur":         "blur",
    "desenfoque":   "blur",
    "unscharf":     "blur",
    "borrar":       "blur",
    "flou":         "blur",
    "ブラー":        "blur",
    "模糊":          "blur",

    # THRESHOLD
    "threshold":    "threshold",
    "umbral":       "threshold",
    "schwelle":     "threshold",
    "limiar":       "threshold",
    "seuil":        "threshold",
    "閾値":          "threshold",
    "阈值":          "threshold",

    # INVERT
    "invert":       "invert",
    "invertir":     "invert",
    "invertieren":  "invert",
    "inverso":      "invert",
    "inverser":     "invert",
    "反転":          "invert",
    "反转":          "invert",

    # INFO
    "info":         "info",
    "información":  "info",
    "informationen":"info",
    "informações":  "info",
    "informations": "info",
    "情報":          "info",
    "信息":          "info",

    # SHOW
    "show":         "show",
    "mostrar":      "show",
    "zeigen":       "show",
    "exibir":       "show",
    "afficher":     "show",
    "表示":          "show",
    "显示":          "show",
}


def resolve(command: str) -> str:
    """Translate any language alias to the canonical command."""
    return ALIASES.get(command.lower(), command.lower())
