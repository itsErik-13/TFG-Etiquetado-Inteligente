"""
text_preprocessor.py

This module contains classes and functions for preprocessing text data.

Author:
- Erik Pereira
"""

import os
import re
import string
import argparse
import pickle
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from nltk.corpus import stopwords


def load_stopwords(language='english', custom_stopwords=None):
    """
    Loads stopwords for a specified language and optionally adds custom stopwords.
    """
    try:
        stop_words = set(stopwords.words(language))
        if custom_stopwords and os.path.exists(custom_stopwords):
            with open(custom_stopwords, 'r', encoding='utf-8') as file:
                custom_words = set(word.strip() for word in file.readlines())
                stop_words.update(custom_words)
        return stop_words
    except OSError:
        print(f"No stopwords found for language '{language}'.")
        return set()

class RemoveUrls(BaseEstimator, TransformerMixin):
    """
    Transformer class to remove URLs from text.
    """
    def fit(self, X, y=None): return self
    def transform(self, X): return [re.sub(r'http[s]?://\S+', '', text) for text in X]

class RemovePunctuation(BaseEstimator, TransformerMixin):
    """
    Transformer class to remove punctuation from text.
    """
    def fit(self, X, y=None): return self
    def transform(self, X): return [text.translate(str.maketrans("", "", string.punctuation)) for text in X]

class RemoveNonASCII(BaseEstimator, TransformerMixin):
    """
    Transformer class to remove non-ASCII characters from text.
    """
    def fit(self, X, y=None): return self
    def transform(self, X): return [text.encode("ascii", "ignore").decode("ascii") for text in X]

class RemoveStopwords(BaseEstimator, TransformerMixin):
    """
    Transformer class to remove stopwords from text.

    Args:
        language (str): Language for stopwords (default: "english").
        custom_stopwords (str): Path to a custom stopwords file (optional).
    """
    def __init__(self, language='english', custom_stopwords=None):
        self.stop_words = load_stopwords(language, custom_stopwords)

    def fit(self, X, y=None): return self
    def transform(self, X):
        return [' '.join([word for word in word_tokenize(text.lower()) if word not in self.stop_words]) for text in X]

class RemoveShortWords(BaseEstimator, TransformerMixin):
    """
    Transformer class to remove words shorter than a specified length.

    Args:
        min_length (int): Minimum word length (default: 3).
    """
    def __init__(self, min_length=3):
        self.min_length = min_length

    def fit(self, X, y=None): return self
    def transform(self, X):
        return [' '.join([word for word in word_tokenize(text) if len(word) >= self.min_length]) for text in X]

class Lemmatizer(BaseEstimator, TransformerMixin):
    """
    Transformer class to lemmatize words in text.
    """
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()

    def fit(self, X, y=None): return self
    def transform(self, X):
        return [' '.join(self.lemmatizer.lemmatize(word) for word in word_tokenize(text)) for text in X]

def create_preprocessing_pipeline(min_word_length, stopwords_language, custom_stopwords):
    """
    Creates a preprocessing pipeline with multiple text cleaning steps.

    Args:
        min_word_length (int): Minimum word length for preprocessing.
        stopwords_language (str): Language for stopwords removal.
        custom_stopwords (str): Path to a custom stopwords file (optional).

    Returns:
        sklearn.pipeline.Pipeline: A pipeline object for preprocessing text.

    Example:
        pipeline = create_preprocessing_pipeline(3, "english", "custom_stopwords.txt")
    """
    return Pipeline([
        ('remove_urls', RemoveUrls()),
        ('remove_punctuation', RemovePunctuation()),
        ('remove_non_ascii', RemoveNonASCII()),
        ('remove_stopwords', RemoveStopwords(language=stopwords_language, custom_stopwords=custom_stopwords)),
        ('remove_short_words', RemoveShortWords(min_length=min_word_length)),
        ('lemmatizer', Lemmatizer()),
    ])
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aplica preprocesamiento de texto a un archivo PKL.")
    parser.add_argument("--input_pkl", type=str, required=True, help="Ruta al archivo PKL de entrada con columnas 'label_post' y 'text'.")
    parser.add_argument("--output_dir", type=str, default="data/datasets", help="Directorio donde guardar los archivos procesados.")
    parser.add_argument("--min_word_length", type=int, default=3, help="Longitud mínima de palabras.")
    parser.add_argument("--stopwords_language", type=str, default="english", help="Idioma de stopwords.")
    parser.add_argument("--custom_stopwords", type=str, default=None, help="Archivo de stopwords personalizados.")

    args = parser.parse_args()
    clean_name = os.path.splitext(os.path.basename(args.input_pkl))[0].replace("_raw", "")


    # Cargar el archivo PKL
    with open(args.input_pkl, "rb") as file:
        data = pickle.load(file)

    # Verificar que las columnas 'label_post' y 'text' existan
    if not all(col in data.columns for col in ['label_post', 'text']):
        raise ValueError("El archivo PKL debe contener columnas 'label_post' y 'text'.")

    pipeline = create_preprocessing_pipeline(
        min_word_length=args.min_word_length,
        stopwords_language=args.stopwords_language,
        custom_stopwords=args.custom_stopwords
    )

    # Aplicar el preprocesamiento a la columna 'text'
    data['text_clean'] = pipeline.fit_transform(data['text'])
    data.drop(columns=['text'], inplace=True)  # Eliminar la columna original 'text'

    # Guardar el resultado en un archivo PKL
    os.makedirs(args.output_dir, exist_ok=True)
    output_pkl = os.path.join(args.output_dir, f"pickle/{clean_name}_preprocessed.pkl")
    with open(output_pkl, "wb") as file:
        # Reordenar las columnas para que 'label_post' sea la primera
        data = data[['label_post', 'text_clean']]
        pickle.dump(data, file)

    # Guardar el resultado en un archivo CSV
    output_csv = os.path.join(args.output_dir, f"csv/{clean_name}_preprocessed.csv")
    data.to_csv(output_csv, index=False)

    print(f"Texto preprocesado guardado en: {output_pkl} y {output_csv}")