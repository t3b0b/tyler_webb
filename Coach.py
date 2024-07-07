import tensorflow as tf
from transformers import TFAutoModelForSequenceClassification, AutoTokenizer
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from flask_login import current_user
from models import BloggPost

# Ladda ner stopwords
nltk.download('stopwords')
stop_words = set(nltk.corpus.stopwords.words('swedish'))

def preprocess_text(text):
    text = re.sub(r'\W', ' ', text)  # Ta bort icke-alfanumeriska tecken
    text = re.sub(r'\s+', ' ', text)  # Ta bort extra mellanslag
    text = text.lower()  # Konvertera till gemener
    text = ' '.join([word for word in text.split() if word not in stop_words])  # Ta bort stop words
    return text

# Ladda den förtränade modellen och tokenisatorn
model_name = "distilbert-base-uncased-finetuned-sst-2-english"
model = TFAutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

def get_sentiment(text):
    inputs = tokenizer(text, return_tensors="tf")
    outputs = model(inputs)
    probs = tf.nn.softmax(outputs.logits, axis=-1)
    return np.argmax(probs, axis=1), np.max(probs, axis=1)

# Hämta och förbehandla bloggposter
blogg_posts = BloggPost.query.filter_by(user_id=current_user.id).all()
texts = [post.content for post in blogg_posts]
preprocessed_texts = [preprocess_text(text) for text in texts]

# Analysera sentimentet i varje inlägg
sentiment_results = [get_sentiment(text) for text in preprocessed_texts]

# Skriv ut resultaten
for i, (sentiment, confidence) in enumerate(sentiment_results):
    sentiment = sentiment[0]  # Hämta värdet från arrayen
    confidence = confidence[0]  # Hämta värdet från arrayen
    sentiment_label = "POSITIVE" if sentiment == 1 else "NEGATIVE"
    print(f"Post {i+1}: {sentiment_label} (Confidence: {confidence:.2f})")

def generate_motivational_message(sentiment):
    if sentiment == 1:  # POSITIVE
        return "Fortsätt det fantastiska arbetet! Din positiva inställning skiner genom allt du gör."
    else:  # NEGATIVE
        return "Det verkar som att du går igenom en tuff tid. Kom ihåg att varje motgång är en möjlighet att växa."

# Generera och skriv ut motiverande meddelanden
for i, (sentiment, confidence) in enumerate(sentiment_results):
    sentiment = sentiment[0]
    message = generate_motivational_message(sentiment)
    print(f"Post {i+1} Motivational Message: {message}")
