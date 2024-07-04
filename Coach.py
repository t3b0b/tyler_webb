from transformers import pipeline
from models import BloggPost, Bullet, Dagbok
import re
import nltk
from nltk.corpus import stopwords
from flask_login import current_user

def preprocess_text(text):
    text = re.sub(r'\W', ' ', text)  # Ta bort icke-alfanumeriska tecken
    text = re.sub(r'\s+', ' ', text)  # Ta bort extra mellanslag
    text = text.lower()  # Konvertera till gemener
    text = ' '.join([word for word in text.split() if word not in stop_words])  # Ta bort stop words
    return text

nltk.download('stopwords')
stop_words = set(stopwords.words('swedish'))
sentiment_analyzer = pipeline('sentiment-analysis')

preprocessed_posts = BloggPost.query.filter_by(user_id=current_user.id).all()
print(preprocessed_posts.content)
# Analysera sentimentet i varje inlägg
sentiment_results = [sentiment_analyzer(post)[0] for post in preprocessed_posts]

preprocessed_posts = [preprocess_text(post[0]) for post in posts]
# Skriv ut resultaten
for i, result in enumerate(sentiment_results):
    print(f"Post {i+1}: {result['label']} (Confidence: {result['score']:.2f})")

