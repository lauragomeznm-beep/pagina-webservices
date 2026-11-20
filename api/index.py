from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageOps
import numpy as np

app = Flask(__name__)


def predecir_digito_desde_imagen(archivo):
    img = Image.open(archivo.stream).convert("L")
    img_invertida = ImageOps.invert(img)
    img_redimensionada = img_invertida.resize((28, 28))

    img_array = np.array(img_redimensionada, dtype=np.float32) / 255.0

    # Se divide la grilla de 28x28 en zonas para estimar el dígito (0-9) y su confianza
    h, w = img_array.shape
    mitad_h, mitad_w = h // 2, w // 2
    tercio_h = h // 3

    arriba = float(np.mean(img_array[:mitad_h, :]))
    abajo = float(np.mean(img_array[mitad_h:, :]))
    centro = float(np.mean(img_array[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]))
    arriba_izq = float(np.mean(img_array[:mitad_h, :mitad_w]))
    abajo_der = float(np.mean(img_array[mitad_h:, mitad_w:]))
    trazos_horizontales = float(
        np.mean(img_array[0:3, :]) + np.mean(img_array[mitad_h - 1 : mitad_h + 2, :]) + np.mean(img_array[-3:, :])
    )

    scores = np.zeros(10, dtype=np.float32)
    scores[0] = centro * 0.2 + (arriba + abajo) * 0.7
    scores[1] = (1.0 - abs(arriba_izq - abajo_der)) * 0.6 + (1.0 - abajo_der) * 0.4
    scores[2] = arriba * 0.5 + abajo * 0.6 + trazos_horizontales * 0.3
    scores[3] = arriba * 0.4 + abajo * 0.5 + abajo_der * 0.5
    scores[4] = arriba_izq * 0.6 + centro * 0.5
    scores[5] = arriba * 0.5 + abajo * 0.5 + (1.0 - arriba_izq) * 0.3
    scores[6] = abajo * 0.7 + arriba_izq * 0.4
    scores[7] = arriba * 0.7 + (1.0 - abajo) * 0.3
    scores[8] = (arriba + abajo + centro) * 0.6
    scores[9] = arriba * 0.7 + abajo_der * 0.4

    # Normalizar a porcentajes con softmax suave
    exp_scores = np.exp((scores - np.max(scores)) * 8.0)
    probs = (exp_scores / np.sum(exp_scores)) * 100.0

    digito = int(np.argmax(probs))
    confianza = float(np.max(probs))
    return digito, round(confianza, 2)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/predecir", methods=["POST"])
def predecir():
    if "imagen" not in request.files:
        return jsonify({"status": "error", "mensaje": "No se envió ninguna imagen."}), 400

    archivo = request.files["imagen"]
    if not archivo or archivo.filename == "":
        return jsonify({"status": "error", "mensaje": "Selecciona un archivo de imagen válido."}), 400

    try:
        digito, confianza = predecir_digito_desde_imagen(archivo)
        return jsonify({
            "status": "ok",
            "numero": digito,
            "confianza": confianza
        })
    except Exception:
        return jsonify({"status": "error", "mensaje": "No se pudo leer la imagen."}), 500


if __name__ == "__main__":
    app.run(debug=True)
