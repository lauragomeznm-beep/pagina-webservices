import io
import numpy as np
from PIL import Image, ImageOps
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Plantillas 8x8 de dígitos del 0 al 9 para reconocimiento ligero sin dependencias pesadas
DIGIT_TEMPLATES = {
    0: [
        "00111100",
        "01100110",
        "11000011",
        "11000011",
        "11000011",
        "11000011",
        "01100110",
        "00111100",
    ],
    1: [
        "00011000",
        "00111000",
        "01111000",
        "00011000",
        "00011000",
        "00011000",
        "00011000",
        "01111110",
    ],
    2: [
        "01111100",
        "11000110",
        "00000110",
        "00001100",
        "00111000",
        "01100000",
        "11000000",
        "11111110",
    ],
    3: [
        "01111100",
        "11000110",
        "00000110",
        "00111100",
        "00000110",
        "00000110",
        "11000110",
        "01111100",
    ],
    4: [
        "00001110",
        "00011110",
        "00110110",
        "01100110",
        "11111111",
        "00000110",
        "00000110",
        "00000110",
    ],
    5: [
        "11111110",
        "11000000",
        "11111100",
        "00000110",
        "00000110",
        "00000110",
        "11000110",
        "01111100",
    ],
    6: [
        "00111100",
        "01100000",
        "11000000",
        "11111100",
        "11000110",
        "11000110",
        "11000110",
        "01111100",
    ],
    7: [
        "11111110",
        "11000110",
        "00001100",
        "00011000",
        "00110000",
        "00110000",
        "00110000",
        "00110000",
    ],
    8: [
        "01111100",
        "11000110",
        "11000110",
        "01111100",
        "11000110",
        "11000110",
        "11000110",
        "01111100",
    ],
    9: [
        "01111100",
        "11000110",
        "11000110",
        "01111110",
        "00000110",
        "00000110",
        "00001100",
        "01111000",
    ],
}

TEMPLATE_MATRICES = {
    digit: np.array([[int(c) for c in row] for row in rows], dtype=np.float32)
    for digit, rows in DIGIT_TEMPLATES.items()
}

HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reconocedor de Números</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gradient-to-br from-rose-50 via-purple-50 to-sky-100 flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-white/95 backdrop-blur rounded-3xl shadow-xl border border-purple-100 p-7">
        <div class="text-center mb-6">
            <h1 class="text-2xl font-bold text-slate-800">Reconocedor de Números</h1>
            <p class="text-sm text-slate-500 mt-1">Sube una imagen con un número del 0 al 9</p>
        </div>

        <form id="uploadForm" class="space-y-4">
            <label for="imageInput" class="flex flex-col items-center justify-center w-full h-44 border-2 border-dashed border-purple-200 rounded-2xl cursor-pointer bg-purple-50/40 hover:bg-purple-50 transition">
                <div id="placeholder" class="text-center p-4">
                    <p class="text-sm font-medium text-purple-700">Haz clic para seleccionar una imagen</p>
                    <p class="text-xs text-slate-400 mt-1">PNG, JPG o WEBP</p>
                </div>
                <img id="preview" class="hidden max-h-36 rounded-xl object-contain" alt="Vista previa" />
                <input id="imageInput" name="image" type="file" accept="image/*" class="hidden" required />
            </label>

            <button type="submit" id="submitBtn" class="w-full py-3 px-4 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold text-sm shadow-sm transition">
                Reconocer Número
            </button>
        </form>

        <div id="resultBox" class="hidden mt-6 p-4 rounded-2xl bg-slate-50 border border-slate-100 text-center">
            <p class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Número detectado</p>
            <p id="predictedDigit" class="text-5xl font-extrabold text-purple-600 mt-1">-</p>
            <p id="confidenceText" class="text-xs text-slate-500 mt-2"></p>
        </div>
    </div>

    <script>
        const imageInput = document.getElementById('imageInput');
        const preview = document.getElementById('preview');
        const placeholder = document.getElementById('placeholder');
        const uploadForm = document.getElementById('uploadForm');
        const resultBox = document.getElementById('resultBox');
        const predictedDigit = document.getElementById('predictedDigit');
        const confidenceText = document.getElementById('confidenceText');
        const submitBtn = document.getElementById('submitBtn');

        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (ev) => {
                preview.src = ev.target.result;
                preview.classList.remove('hidden');
                placeholder.classList.add('hidden');
            };
            reader.readAsDataURL(file);
        });

        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!imageInput.files[0]) return;

            submitBtn.disabled = true;
            submitBtn.textContent = 'Analizando...';

            const formData = new FormData();
            formData.append('image', imageInput.files[0]);

            try {
                const res = await fetch('/api/predecir', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (res.ok) {
                    predictedDigit.textContent = data.digit;
                    confidenceText.textContent = `Confianza aproximada: ${data.confidence}%`;
                    resultBox.classList.remove('hidden');
                } else {
                    alert(data.error || 'No se pudo procesar la imagen.');
                }
            } catch (err) {
                alert('Error de conexión con el servidor.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Reconocer Número';
            }
        });
    </script>
</body>
</html>
"""

def predict_digit_from_image(file_bytes):
    img = Image.open(io.BytesIO(file_bytes)).convert("L")
    arr = np.array(img, dtype=np.float32)

    # Si el fondo es claro (promedio > 127), invertimos para que el trazo sea blanco (1)
    if arr.mean() > 127:
        arr = 255.0 - arr

    # Binarizar y recortar al área del número
    mask = arr > (arr.max() * 0.35 if arr.max() > 0 else 128)
    coords = np.argwhere(mask)
    if coords.size > 0:
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0) + 1
        cropped = Image.fromarray((mask[y0:y1, x0:x1] * 255).astype(np.uint8))
    else:
        cropped = Image.fromarray((mask * 255).astype(np.uint8))

    # Redimensionar a 8x8 manteniendo proporción centrada
    resized = ImageOps.pad(cropped, (8, 8), color=0)
    norm = np.array(resized, dtype=np.float32) / 255.0

    best_digit = 0
    best_score = -1.0
    scores = {}

    for digit, tmpl in TEMPLATE_MATRICES.items():
        diff = np.abs(norm - tmpl).mean()
        similarity = max(0.0, 1.0 - diff)
        scores[digit] = similarity
        if similarity > best_score:
            best_score = similarity
            best_digit = digit

    confidence = round(min(99.0, max(50.0, best_score * 100)), 1)
    return best_digit, confidence

@app.route("/")
@app.route("/api/index")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/api/predecir", methods=["POST"])
def predecir():
    if "image" not in request.files:
        return jsonify({"error": "No se recibió ninguna imagen."}), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Selecciona un archivo válido."}), 400
    try:
        digit, confidence = predict_digit_from_image(file.read())
        return jsonify({"digit": digit, "confidence": confidence})
    except Exception as e:
        return jsonify({"error": f"Error al analizar la imagen: {str(e)}"}), 500
