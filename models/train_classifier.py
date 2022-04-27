import sys
import pandas as pd
import numpy as np

from sqlalchemy import create_engine

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tokenize import word_tokenize

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

from sklearn import metrics
from sklearn.pipeline import Pipeline
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import classification_report
from sklearn.metrics import multilabel_confusion_matrix
from sklearn.model_selection import train_test_split, GridSearchCV

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBRegressor
from sklearn.svm import SVC

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

import pickle


def load_data(database_filepath):
    # load data from database
    engine = create_engine(f'sqlite:///{database_filepath}')
    table_name = f'{database_filepath}'.replace("\\", " ").replace("/", " ").split(" ")[-1].split(".")[0]
    df = pd.read_sql_table(table_name,  engine)

    X = df["message"]
    y = df.drop(["id", "message", "original", "genre"], axis=1)

    return X, y, y.columns



def tokenize(text):

    # normalize case and remove punctuation
    text = re.sub(r"[^a-zA-Z0-9]", " ", text.lower())
    
    # tokenize text
    tokens = word_tokenize(text)
    
    # lemmatize andremove stop words
    tokens = [WordNetLemmatizer().lemmatize(word) for word in tokens if word not in stopwords.words("english")]

    return tokens

def build_model():

    clf = RandomForestClassifier()

    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('model', MultiOutputClassifier(clf))
    ])

   
    return pipeline

def evaluate_model(model, X_test, y_test, category_names):
     # predict on test data
    y_pred = model.predict(X_test)

    for col in range(y_pred.shape[1]):
        y_true = y_test.to_numpy()[:,col]
        y_hat = y_pred[:,col]
        col_name = category_names[col]
       
        print(
            f"Classification report for predicting {col_name}:\n"
            f"{metrics.classification_report(y_true, y_hat, zero_division = 0)}\n"
            f"{multilabel_confusion_matrix(y_true, y_hat)} \n"
        )


def save_model(model, model_filepath):
    pickle.dump(model, open(model_filepath, 'wb'))


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print("""
        Please provide the filepath of the disaster messages database as the first argument 
        and the filepath of the pickle file to save the model to as the second argument.
        \n\nExample: python train_classifier.py data\DisasterResponse.db classifier.pkl
        """)


if __name__ == '__main__':
    main()