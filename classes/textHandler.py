from extensions import db
from datetime import datetime,timedelta
from models import MyWords
from random import choice
import random

class textHandler:
    def __init__(self, user_id):
        self.user_id = user_id

# region Txt
    def readWords(self, filename):
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'utf-8-sig']

        for encoding in encodings:
            try:
                with open(filename, 'r', encoding=encoding) as file:
                    words = [line.strip() for line in file if line.strip()]  # Tar bort tomma rader

                if not words:
                    raise ValueError(f"File {filename} is empty.")

                first_word = words[0]  # Första ordet i listan
                word_list = words[1:]  # Resterande ord

                return first_word, word_list  # Returnera både första ordet och hela listan

            except UnicodeDecodeError:
                continue  # Prova nästa encoding om det blir fel

        raise UnicodeDecodeError(f"Could not decode the file {filename} with any of the tried encodings.")

    def unique(db, by_db):
        unique_data = [post.title for post in db.query.with_entities(by_db).distinct().all()]
        list = [item[0] for item in unique_data]
        return list

    def add_words_from_file(self, file_name, user_id):
        try:
            _, word_list = self.readWords(file_name)  # Läs in ordlistan från filen
            if not word_list:
                return "No words found in file."

            # Hämta alla ord som redan finns i databasen för denna användare
            existing_words = set(word.word for word in MyWords.query.filter_by(user_id=user_id).all())

            # Filtrera ut ord som redan finns
            new_words = [word for word in word_list if word not in existing_words]

            if not new_words:
                return "All words already exist in the database."

            # Skapa nya objekt och batcha in dem i databasen
            db.session.bulk_save_objects([MyWords(word=word, user_id=user_id) for word in new_words])
            db.session.commit()

            return f"{len(new_words)} words added successfully."
        except FileNotFoundError:
            return "File not found."
        except Exception as e:
            db.session.rollback()
            return f"An unexpected error occurred: {e}"

    def add_unique_word(self, word):
        # Kontrollera om ordet redan finns
        existing_word = MyWords.query.filter_by(word=word).first()
        if existing_word:
            return f"Word '{word}' already exists!", False  # Returnera ett felmeddelande

        # Skapa nytt ord
        new_word = MyWords(word=word, user_id = self.user_id)
        db.session.add(new_word)
        db.session.commit()
        return f"Word '{word}' added successfully!", True

    def section_content(db,section):
        list = db.query.filter_by(name=section).first()
        return list


    def getWord(self):
        ord_lista = MyWords.query.filter_by(user_id = self.user_id).all()
        ordet = None
        for ord in ord_lista:
            if not ord.used:
                # Uppdatera ordet till att vara använt
                ord.used = True
                db.session.commit()

                ordet = ord.word
                break
        return ordet, ord_lista
    
    def get_daily_question():

        Questions = {
        "Prioriteringar": ["Viktigt att prioritera idag",
                    'Viktigt att prioritera imorgon'],
        "Tacksam": ["Vad har du att vara tacksam för?"],
        "Tankar": ["Tankar/insikter värda att påminnas om",
                "Tankar/insikter att ta med till imorgon"],
        "Bättre": ["Vad ska du se till att göra bättre idag?",
                "Vad ska du se till att göra bättre imorgon?"],
        "Känslor": ["Hur känner du dig idag?",
                    "Hur känner du inför imorgon?"],
        "Mål": ["Vilka mål vill du nå idag?",
                "Vilka mål vill du nå imorgon?"],
        "Relationer": ["Finns det någon du vill ge extra uppmärksamhet till idag?",
                    "Finns det någon du vill ge extra uppmärksamhet till imorgon?"],
        "Lärande": ["Vad vill du lära dig eller utforska idag?",
                    "Vad vill du lära dig eller utforska imorgon?"],
        "Hälsa": ["Vad kan du göra idag för att ta hand om din hälsa och energi?",
                "Vad kan du göra imorgon för att ta hand om din hälsa och energi?"],
        "Uppskattning": ["Vad eller vem kan du visa uppskattning för idag?",
                        "Vad eller vem kan du visa uppskattning för imorgon?"],
        "Kreativitet": ["Hur kan du uttrycka din kreativitet idag?",
                        "Hur kan du uttrycka din kreativitet imorgon?"],
        "Utmaningar": ["Finns det någon utmaning du kan ta itu med idag?",
                    "Finns det någon utmaning du kan ta itu med imorgon?"],
        "Avslappning": ["Vad kan du göra för att slappna av och återhämta dig idag?",
                        "Vad kan du göra för att slappna av och återhämta dig imorgon?"],
        "Underlätta": ["Vad kan du göra idag för att underlätta morgondagen?",
                        "Vad kan du göra för att underlätta den här dagen?"],
    }
        
        today = datetime.today().date()
        tomorrow = today + timedelta(days=1)
        hour = datetime.now().hour
        
        random.seed(str(today))  # Samma fråga varje dag
        list_type = random.choice(list(Questions.keys()))  # Välj en slumpmässig kategori

        if hour < 14:
            message = Questions[list_type][0]  # Första frågan
            list_date = today
        else:
            message = Questions[list_type][1] if len(Questions[list_type]) > 1 else Questions[list_type][0]
            list_date = tomorrow  # Sätter frågan till morgondagens datum om klockan är efter 14:00

        return message, list_type, list_date

# endregion
