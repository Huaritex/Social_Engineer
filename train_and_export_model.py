import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
import numpy as np
import os

# --- 1. Generación de Datos de Ejemplo ---
# En un proyecto real, cargarías un dataset real de phishing y legítimo.
phishing_examples = [
    "¡Alerta! Tu cuenta bancaria ha sido comprometida. Haz clic aquí para verificar: http://malicious.link",
    "Felicidades, has ganado un premio. Reclámalo en este enlace: http://scam.site",
    "Actualiza tus datos de seguridad ahora: https://fakebank.com/login",
    "Tu paquete está en espera. Confirma tu envío aquí: http://delivery-scam.net",
    "Hemos detectado actividad sospechosa en tu cuenta. Inicia sesión inmediatamente: http://login-warning.org",
    "La factura de tu último pedido está lista. Descárgala desde: http://invoice-scam.co",
    "Tu contraseña caducará pronto. Cámbiala aquí: https://update-password.info",
    "Importante: Problema con tu pago. Revisa aquí: http://payment-issue.biz",
    "Verifica tu identidad para evitar la suspensión de la cuenta: http://verify-account.io",
    "Oferta limitada: Obtén un 50% de descuento si haces clic en este enlace: http://discount-spam.xyz"
]

legitimate_examples = [
    "Hola, ¿cómo estás?",
    "Reunión programada para mañana a las 10 AM.",
    "Adjunto el informe trimestral.",
    "No olvides comprar leche de camino a casa.",
    "Confirmación de tu reserva para el vuelo XZ789.",
    "El clima para el fin de semana será soleado.",
    "Recordatorio: Pago de la suscripción mensual.",
    "Hemos actualizado nuestros términos y condiciones.",
    "¿Podrías revisar el documento que te envié?",
    "Gracias por tu compra. Tu pedido #12345 ha sido enviado."
]

# Combinar ejemplos y crear etiquetas (1 para phishing, 0 para legítimo)
texts = phishing_examples + legitimate_examples
labels = [1] * len(phishing_examples) + [0] * len(legitimate_examples)

# Convertir a arrays de NumPy
labels = np.array(labels)

# --- 2. Preprocesamiento de Texto ---
# Parámetros del tokenizador
vocab_size = 1000 # El tamaño del vocabulario, ajusta según tu dataset real
embedding_dim = 16 # Dimensión de los embeddings de palabras
max_length = 50   # Longitud máxima de las secuencias de texto
trunc_type = 'post'
padding_type = 'post'
oov_tok = "<OOV>" # Token para palabras fuera de vocabulario

# Inicializar y ajustar el tokenizador
tokenizer = Tokenizer(num_words = vocab_size, oov_token=oov_tok)
tokenizer.fit_on_texts(texts)

# Guardar el word_index para usarlo en JavaScript (muy importante para la inferencia)
word_index = tokenizer.word_index
# Puedes guardar esto en un archivo JSON y cargarlo en JS
# import json
# with open('word_index.json', 'w') as f:
#     json.dump(word_index, f)

# Convertir textos a secuencias de números
sequences = tokenizer.texts_to_sequences(texts)

# Pad (rellenar) las secuencias para que tengan la misma longitud
padded_sequences = pad_sequences(sequences, maxlen=max_length, padding=padding_type, truncating=trunc_type)

# --- 3. División de Datos (Entrenamiento y Prueba) ---
X_train, X_test, y_train, y_test = train_test_split(padded_sequences, labels, test_size=0.2, random_state=42)

# --- 4. Construir y Entrenar el Modelo Keras ---
model = tf.keras.Sequential([
    tf.keras.layers.Embedding(vocab_size, embedding_dim, input_length=max_length),
    tf.keras.layers.GlobalAveragePooling1D(), # O GlobalMaxPooling1D o Flatten
    tf.keras.layers.Dense(24, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid') # Una neurona con sigmoid para clasificación binaria
])

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

model.summary()

num_epochs = 30 # Puedes ajustar esto
history = model.fit(X_train, y_train, epochs=num_epochs, validation_data=(X_test, y_test), verbose=2)

# --- 5. Exportar el Modelo a Formato TensorFlow.js ---
# Crear el directorio de salida si no existe
output_dir = 'social engineer/model' # Aquí es donde tu HTML buscará el modelo
os.makedirs(output_dir, exist_ok=True)

# Guardar el modelo en formato Keras SavedModel primero
keras_model_path = os.path.join(output_dir, 'phishing_model.h5')
model.save(keras_model_path)
print(f"Modelo Keras guardado en: {keras_model_path}")

# Convertir el modelo a TensorFlow.js
# Asegúrate de que `tensorflowjs` esté instalado (`pip install tensorflowjs`)
# El comando se ejecutaría desde la línea de comandos, pero aquí lo haremos programáticamente para ilustrar
try:
    print(f"Convirtiendo modelo a TensorFlow.js en: {output_dir}")
    # Nota: tensorflowjs.converters.save_keras_model es para usar dentro de Python
    # Para el SavedModel de TF 2.x, el comando es: tensorflowjs_converter --input_format=tf_saved_model --output_format=tfjs_graph_model <saved_model_dir> <output_dir>
    # Sin embargo, dado que guardamos como .h5, usaremos:
    # tensorflowjs_converter --input_format=keras --output_format=tfjs_layers_model <keras_model_path> <output_dir>

    # Para ejecutarlo directamente desde Python, es más fácil usar un comando de sistema:
    import subprocess
    subprocess.run([
        'tensorflowjs_converter',
        '--input_format=keras',
        '--output_format=tfjs_layers_model', # Esto es importante si el modelo es Sequential/Functional Keras
        keras_model_path,
        output_dir
    ], check=True) # check=True lanzará un error si el comando falla
    print("Modelo convertido a TensorFlow.js exitosamente.")
except Exception as e:
    print(f"Error al convertir el modelo a TensorFlow.js: {e}")
    print("Por favor, asegúrate de que 'tensorflowjs' esté instalado y que el comando 'tensorflowjs_converter' esté en tu PATH.")
    print(f"También puedes intentar ejecutar el comando de conversión manualmente desde la terminal:")
    print(f"tensorflowjs_converter --input_format=keras --output_format=tfjs_layers_model \"{keras_model_path}\" \"{output_dir}\"")

print("\n--- PRUEBA BÁSICA DEL MODELO ---")
# Simula una nueva entrada (similar a lo que el usuario ingresaría)
test_message_phishing = "Urgent: Your account is locked. Click here to unlock now: http://lock.com"
test_message_legit = "Hello, how are you today?"

test_sequences_phishing = tokenizer.texts_to_sequences([test_message_phishing])
test_padded_phishing = pad_sequences(test_sequences_phishing, maxlen=max_length, padding=padding_type, truncating=trunc_type)
prediction_phishing = model.predict(test_padded_phishing)[0][0]
print(f"Mensaje de phishing: '{test_message_phishing}'")
print(f"Predicción (probabilidad de phishing): {prediction_phishing:.4f}")
print(f"Resultado: {'Phishing' if prediction_phishing > 0.5 else 'Legítimo'}")

test_sequences_legit = tokenizer.texts_to_sequences([test_message_legit])
test_padded_legit = pad_sequences(test_sequences_legit, maxlen=max_length, padding=padding_type, truncating=trunc_type)
prediction_legit = model.predict(test_padded_legit)[0][0]
print(f"Mensaje legítimo: '{test_message_legit}'")
print(f"Predicción (probabilidad de phishing): {prediction_legit:.4f}")
print(f"Resultado: {'Phishing' if prediction_legit > 0.5 else 'Legítimo'}") 