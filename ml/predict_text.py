"""
predict_text.py

This script allows predicting the label of a given text using a pre-trained machine learning model.
It supports multiple models saved in `.joblib` format and applies a preprocessing pipeline to clean the input text.

Functions:
- load_model: Loads a pre-trained model from a `.joblib` file.
- predict_text: Predicts the label of the given text using the loaded model.
- main: Main function to handle command-line arguments and perform predictions.

Usage:
    python predict_text.py --model_path <path_to_model.joblib> --text <text_to_predict>

Arguments:
    --model_path: Path to the `.joblib` file containing the pre-trained model.
    --text: Text to predict (can be multiple words or sentences).

Author:
- Erik Pereira
"""

from xml.parsers.expat import model
import joblib
import argparse
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ml.text_preprocessor import create_preprocessing_pipeline

def load_model(model_path):
    """
    Loads a pre-trained model from a `.joblib` file.

    Args:
        model_path (str): Path to the `.joblib` file.

    Returns:
        sklearn.base.BaseEstimator: The loaded model.

    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"The file {model_path} does not exist.")
    return joblib.load(model_path)

def predict_text(model, text):
    """
    Predicts the label of the given text using the loaded model.

    Args:
        model (sklearn.base.BaseEstimator): The pre-trained model.
        text (list): List of strings to predict.

    Returns:
        list: Predictions for the input text.
    """
    predictions = model.predict(text)
    return predictions

def main(model_path, text):
    """
    Main function to load the model, preprocess the text, and perform predictions.

    Args:
        model_path (str): Path to the `.joblib` file containing the pre-trained model.
        text (list): List of strings to predict.

    Returns:
        None
    """
    # Load the pre-trained model
    model = load_model(model_path)

    # Create the preprocessing pipeline
    pipeline = create_preprocessing_pipeline(min_word_length=3, stopwords_language='english', custom_stopwords=None)

    # Preprocess the input text
    clean_text = pipeline.fit_transform(text)

    # Perform predictions
    predictions = predict_text(model, clean_text)

    # Display results
    for original, prediction in zip(text, predictions):
        print(f"Text: {original}\n → Prediction: {prediction}\n")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Classify text using a pre-trained machine learning model.")
    parser.add_argument('--model_path', type=str, required=True, help="Path to the .joblib file containing the model.")
    parser.add_argument('--text', type=str, nargs='+', required=True, help="Text to predict (can be multiple sentences).")

    args = parser.parse_args()
    main(args.model_path, args.text)
