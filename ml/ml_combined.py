"""
ml_combined.py

This script combines the functionality of Naive Bayes, Random Forest, and SVM models into a single script.
It allows the user to select the model via a command-line argument and performs training, hyperparameter tuning, 
and evaluation using GridSearchCV.

Usage:
    python ml_combined.py --dataset_path <path_to_dataset> --model <nb|rf|svm>

Arguments:
    --dataset_path: Path to the CSV file containing the dataset.
    --model: Model to use (nb for Naive Bayes, rf for Random Forest, svm for Support Vector Machine).

Author:
- Erik Pereira
"""

import os
import pandas as pd
import joblib
import argparse
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from yellowbrick.classifier import ConfusionMatrix

# Transformer to convert sparse matrices to dense
class DenseTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X, y=None): return X.toarray()

def build_model(model_type):
    """
    Builds a machine learning pipeline based on the selected model type.

    Args:
        model_type (str): Type of model to build ('nb', 'rf', 'svm').

    Returns:
        sklearn.pipeline.Pipeline: A pipeline object with the selected model.
    """
    vectorizer = TfidfVectorizer()
    
    if model_type == "nb":
        clf = GaussianNB()
        pipeline = Pipeline([
            ("vectorizer", vectorizer),
            ("to_dense", DenseTransformer()),
            ("classifier", clf),
        ])
    elif model_type == "rf":
        clf = RandomForestClassifier(class_weight="balanced", random_state=42)
        pipeline = Pipeline([
            ("vectorizer", vectorizer),
            ("classifier", clf),
        ])
    elif model_type == "svm":
        clf = LinearSVC(class_weight="balanced", random_state=42)
        pipeline = Pipeline([
            ("vectorizer", vectorizer),
            ("classifier", clf),
        ])
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    return pipeline

def main(dataset_path, model_type):
    """
    Main function to train and evaluate the selected model.

    Args:
        dataset_path (str): Path to the dataset CSV file.
        model_type (str): Type of model to use ('nb', 'rf', 'svm').

    Returns:
        None
    """
    # Load the dataset
    df = pd.read_csv(dataset_path)

    # Split into features (X) and labels (y)
    X = df["text_clean"].fillna("").astype(str)
    y = df["label_post"].fillna("").astype(str)

    target_names = y.unique()

    # Split into training and validation sets (80% training, 20% validation)
    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Build the model
    model = build_model(model_type)

    # Define hyperparameters for GridSearchCV
    if model_type == "nb":
        parameters = {
            "classifier__var_smoothing": [1e-9, 1e-8, 1e-7],
        }
    elif model_type == "rf":
        parameters = {
            "classifier__n_estimators": [100, 200, 300],
            "classifier__max_depth": [None, 10, 20],
            "classifier__min_samples_split": [2, 5],
            "classifier__min_samples_leaf": [1, 2],
        }
    elif model_type == "svm":
        parameters = {
            "classifier__C": [0.01, 0.1, 1],
            "classifier__tol": [1e-4, 1e-3],
            "classifier__max_iter": [1000, 5000],
        }

    # Perform GridSearchCV
    grid_search = GridSearchCV(model, parameters, cv=10, n_jobs=1)
    grid_search.fit(X_train, y_train)

    print("Best parameters found: ", grid_search.best_params_)
    print("Best score found: ", grid_search.best_score_)

    # Save the best model
    dataset_name = os.path.basename(dataset_path).split(".")[0]
    os.makedirs("data/trained_model", exist_ok=True)
    joblib.dump(grid_search.best_estimator_, f"data/trained_model/best_model_{model_type}_{dataset_name}.joblib")

    best_model = grid_search.best_estimator_
    
    vectorizer = best_model.named_steps["vectorizer"]
    X_train_tfidf = vectorizer.transform(X_train)

    # Guardar la matriz TF-IDF
    tfidf_matrix_df = pd.DataFrame(X_train_tfidf.toarray(), columns=vectorizer.get_feature_names_out())
    tfidf_matrix_df.to_csv(f"data/results/tfidf_matrix_{model_type}_{dataset_name}.csv", index=False)

    # Generate Confusion Matrix using Yellowbrick
    os.makedirs("data/results", exist_ok=True)
    cm_viz = ConfusionMatrix(best_model, classes=target_names, percent=True)
    cm_viz.fit(X_train, y_train)
    cm_viz.score(X_valid, y_valid)
    cm_viz.poof(outpath=f"data/results/confusion_matrix_{model_type}_{dataset_name}.png")

    # Generate Classification Report using sklearn
    cr = classification_report(y_valid, best_model.predict(X_valid), target_names=target_names)
    with open(f"data/results/classification_report_{model_type}_{dataset_name}.txt", "w") as file:
        file.write(cr)

    print(f"Results saved in 'data/results' directory.")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run ML models with GridSearchCV")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to the dataset CSV file")
    parser.add_argument("--model", type=str, required=True, choices=["nb", "rf", "svm"], help="Model to use (nb, rf, svm)")
    args = parser.parse_args()

    main(args.dataset_path, args.model)