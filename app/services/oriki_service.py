import random
from app.utils.loader import load_data
from app.utils.generator import generate_oriki

def get_oriki(language, name=None):
    df = load_data(language)

    if name:
        result = df[df['name'].str.lower() == name.lower()]
        if not result.empty:
            return result.iloc[0]['praise_text']
    
    # fallback: random
    return random.choice(df['praise_text'].tolist())

def generate_smart_oriki(language):
    df = load_data(language)
    return generate_oriki(df['praise_text'].tolist())