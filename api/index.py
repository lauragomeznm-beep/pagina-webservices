from flask import Flask

app = Flask(__name__)

@app.route("/")
@app.route("/api/index")
def home():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reconocedor de Números</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="min-h-screen bg-gradient-to-br from-rose-50 via-purple-50 to-sky-100 flex items-center justify-center p-4">
        <div class="w-full max-w-md bg-white rounded-3xl shadow-lg p-7 text-center">
            <h1 class="text-2xl font-bold text-slate-900 mb-2">Reconocedor de Números</h1>
            <p class="text-sm text-slate-500">¡La página ya cargó correctamente!</p>
        </div>
    </body>
    </html>
    """
