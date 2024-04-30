import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Données d'entraînement
sentences = ["chez l'hôtel", "à l'agence", "au restaurant", "chez Boondooa"]
labels = ["chez", "à", "en", "chez"]

# Tokenisation et encodage des phrases
tokenizer = Tokenizer()
tokenizer.fit_on_texts(sentences)
word_index = tokenizer.word_index
sequences = tokenizer.texts_to_sequences(sentences)

# Ajout de padding pour obtenir des séquences de même longueur
max_length = max([len(seq) for seq in sequences])
padded_sequences = pad_sequences(sequences, maxlen=max_length, padding='post')

# Création du modèle
model = tf.keras.Sequential([
    tf.keras.layers.Embedding(len(word_index)+1, 64, input_length=max_length),
    tf.keras.layers.LSTM(128),
    tf.keras.layers.Dense(len(set(labels)), activation='softmax')
])

# Compilation du modèle
model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# Entraînement du modèle
model.fit(padded_sequences, labels, epochs=10, verbose=1)

# Utilisation du modèle pour prédire la préposition du mot suivant
test_sentence = "à l'agence"
test_sequence = tokenizer.texts_to_sequences([test_sentence])
padded_test_sequence = pad_sequences(test_sequence, maxlen=max_length, padding='post')
predictions = model.predict(padded_test_sequence)
predicted_label_index = tf.argmax(predictions, axis=1).numpy()[0]
predicted_label = list(set(labels))[predicted_label_index]
print("Préposition prédite:", predicted_label)
