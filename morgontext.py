from docx import Document
import re
import datetime
def extract_sections(doc_path):
    doc = Document(doc_path)
    headings = []  # Lista för att spara rubriker
    texts = []  # Lista för att spara texter
    current_text = []

    for para in doc.paragraphs:
        # Anta att rubriker är formaterade med en specifik stil eller fontstorlek
        if para.style.name == 'MS Rubrik':  # Anpassa detta villkor efter dokumentets stil
            if current_text:
                # Lägger till texten som hör till föregående rubrik
                texts.append(current_text)
                current_text = []
            # Lägger till rubriken i listan
            headings.append(para.text)
        else:
            current_text.append(para.text)

    # Spara texten för den sista rubriken
    if current_text:
        texts.append(current_text)

    return headings, texts

def extract_title(header, headings, texts):
    header_index = headings.index(header)
    text = texts[header_index]

    blog_posts = []
    date_pattern = re.compile(r'(\d{2}) / (\d{2}) / (\d{2})\t')
    buffer_text = ""

    for line in text:
        match = date_pattern.search(line)
        if match:
            if buffer_text:
                # Anta att datumet är på formatet DD / MM / YY
                date_str = f"20{match.group(3)}/{match.group(2)}/{match.group(1)}"
                blog_posts.append({
                    "title": header,
                    "date": datetime.datetime.strptime(date_str, '%Y/%m/%d'),
                    "content": buffer_text.strip()
                })
            buffer_text = line[len(match.group(0)):]  # Börja samla text efter datumet
        else:
            buffer_text += " " + line

    if buffer_text:  # Hantera den sista delen
        blog_posts.append({
            "title": header,
            "date": None,
            "content": buffer_text.strip()
        })

    return blog_posts

# Använd funktionen
doc_path = 'Morgon Sidor 2021 (Sorterad).docx'
headings, texts = extract_sections(doc_path)

# Skapa BloggPost-objekt och spara dem i en databas eller annan struktur
Stolt=extract_title('Stolt',headings,texts)
Modig=extract_title('Modig',headings,texts)
Tacksam=extract_title('Tacksam',headings,texts)
Familj=extract_title('Familj ',headings,texts)
Positiv=extract_title('Positiv',headings,texts)
Tålamod=extract_title('Tålamod',headings, texts)
Disciplin=extract_title('Disciplin',headings, texts)
Engagerad=extract_title('Engagerad',headings,texts)
Rörelse=extract_title('Rörelse',headings, texts)
Passionerad=extract_title('Passionerad',headings,texts)
Värdefull=extract_title('Värdefull',headings, texts)
Meningsfull=extract_title('Meningsfull / Syfte',headings,texts)
Tid=extract_title('Tid',headings, texts)
Potential=extract_title('Potential',headings,texts)
Uppoffring=extract_title('Uppoffring',headings,texts)
Nyfiken=extract_title('Nyfiken',headings,texts)
Respekt=extract_title('Respekt',headings, texts)
Uppmärksam=extract_title('Uppmärksam',headings, texts)
Autentisk=extract_title('Autentisk',headings,texts)
Vinna=extract_title('Vinna',headings,texts)
Lojalitet=extract_title('Lojalitet',headings,texts)
Ansvar=extract_title('Ansvar',headings,texts)
Framgångsrik=extract_title('Framgångsrik',headings,texts)
Motiverad=extract_title('Motiverad',headings,texts)
Älska=extract_title('Älska',headings,texts)
Moral=extract_title('Moral',headings,texts)
Vilja=extract_title('Vilja',headings,texts)
Ödmjuk=extract_title('Ödmjuk',headings,texts)
Det_fina_du_har=extract_title('Det fina du har',headings,texts)
Kamp=extract_title('Kamp',headings,texts)
Varför=extract_title('Varför',headings,texts)
Spelet=extract_title('Spelet',headings,texts)
Målinriktad=extract_title('Målinriktad',headings,texts)
Ärligt_Talat=extract_title('Ärligt Talat',headings,texts)
Ambitiös=extract_title('Ambitiös',headings,texts)
Tillit=extract_title('Tillit',headings,texts)
Fokus=extract_title('Fokus',headings,texts)
Att_säga_Nej=extract_title('Att säga Nej',headings,texts)
Genuin=extract_title('Genuin',headings,texts)
Döden=extract_title('Döden',headings,texts)
Morgonen=extract_title('Morgonen',headings,texts)
Prioritera=extract_title('Prioritera',headings,texts)
Regler=extract_title('Regler',headings,texts)
Lek=extract_title('Lek',headings,texts)
Ja_må_han_leva=extract_title('Ja, må han leva',headings,texts)
Min_Historia=extract_title('Min Historia',headings,texts)
Till_Mig_Från_Mig=extract_title('Till Mig Från Mig',headings,texts)
Press=extract_title('Press',headings,texts)
När_jag_faller=extract_title('När jag faller',headings,texts)
Offer=extract_title('Offer',headings,texts)
Min_Grind=extract_title('Min Grind',headings,texts)
Hur_gör_jag=extract_title('Hur gör jag?',headings,texts)
Förändring=extract_title('Förändring',headings,texts)
Inre_Dialog=extract_title('Inre Dialog',headings,texts)
Början=extract_title('Början',headings,texts)

#for post_info in Stolt:
 #   post = BloggPost(author="Tyler O'Brien", title=post_info['title'], date=post_info['date'], content=post_info['content'])

  #  print(f"Title:{post.title}, Date: {post.date}, Content: {post.content}")
