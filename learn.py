import pandas as pd
import tensorflow as tf
from transformers import BertTokenizer, TFBertForSequenceClassification

# Charger les données
data = pd.read_csv("tableur.csv")

# Prétraitement des données
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
encoded_inputs = tokenizer(data["Société"].tolist(), padding=True, truncation=True, return_tensors="tf")

# Construction du modèle
model = TFBertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=1)

# Entraînement du modèle
model.compile(optimizer=tf.keras.optimizers.Adam(),
              loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
              metrics=['accuracy'])
model.fit(encoded_inputs, data["preposition"].values, epochs=3, batch_size=32, validation_split=0.2)
