from flask import Flask, render_template, request
import joblib
import preprocessor

app = Flask(__name__)

# Load models and components
naive_bayes_pipeline = joblib.load("models/naive_bayes_maltese_sentiment_analyzer.joblib")
random_forest_model = joblib.load("models/randomForestModel_Extended.pkl")
random_forest_vectorizer = joblib.load("models/vectorizer_Extended.pkl")
svm_pipeline = joblib.load("models/svm_maltese_sentiment_analyzer.joblib")

@app.route('/')
def home():
    return render_template('analyze.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    result = None
    if request.method == 'POST':
        text = request.form.get('text')
        model_type = request.form.get('model_type')

        try:
            if model_type == 'naive_bayes':
                # Use Naive Bayes pipeline
                custom_preprocessor = naive_bayes_pipeline.named_steps['custom_maltese_preprocessor']
                sentiment_model = naive_bayes_pipeline.named_steps['sentiment_model']

                intermediate_output = custom_preprocessor.transform([text])
                processed_text = intermediate_output.iloc[0]

                prediction = sentiment_model.predict(intermediate_output)[0]
                probabilities = sentiment_model.predict_proba(intermediate_output)[0]
                sentiment_str = "positive" if int(prediction) == 1 else "negative"
                confidence = float(max(probabilities)) * 100

                result = {
                    'input_text': text,
                    'processed_text': processed_text,
                    'sentiment': sentiment_str,
                    'confidence': round(confidence, 2),
                    'model_used': "Naive Bayes"
                }

            elif model_type == 'random_forest':
                # Use Random Forest
                sentence = preprocessor.emoji_to_text(text)
                tokens = preprocessor.tokenise(sentence)
                tokens = preprocessor.clean_tokens(tokens)
                tokens = preprocessor.selective_lowercase(tokens)
                tokens = [preprocessor.get_lemma(token) for token in tokens]
                processed_text = " ".join(tokens)

                X_input = random_forest_vectorizer.transform([processed_text])
                prediction = random_forest_model.predict(X_input)

                sentiment_value = prediction[0]
                sentiment_str = "positive" if str(sentiment_value) == "1" else "negative"

                if hasattr(random_forest_model, "predict_proba"):
                    confidence = random_forest_model.predict_proba(X_input).max() * 100
                else:
                    confidence = "N/A"

                result = {
                    'input_text': text,
                    'processed_text': processed_text,
                    'sentiment': sentiment_str,
                    'confidence': round(confidence, 2) if isinstance(confidence, float) else confidence,
                    'model_used': "Random Forest"
                }
            elif model_type == 'svm':
                # Use SVM pipeline
                custom_preprocessor = svm_pipeline.named_steps['custom_maltese_preprocessor']
                sentiment_model = svm_pipeline.named_steps['sentiment_model']

                intermediate_output = custom_preprocessor.transform([text])
                processed_text = intermediate_output.iloc[0]

                prediction = sentiment_model.predict(intermediate_output)[0]
                probabilities = sentiment_model.predict_proba(intermediate_output)[0]
                sentiment_str = "positive" if int(prediction) == 1 else "negative"
                confidence = float(max(probabilities)) * 100

                result = {
                    'input_text': text,
                    'processed_text': processed_text,
                    'sentiment': sentiment_str,
                    'confidence': round(confidence, 2),
                    'model_used': "SVM"
                }
            
            else:
                result = {
                    'input_text': text,
                    'sentiment': 'Error',
                    'confidence': 'Invalid model selection',
                    'model_used': 'Unknown'
                }

        except Exception as e:
            result = {
                'input_text': text,
                'sentiment': 'Error',
                'confidence': f'Error processing text: {str(e)}',
                'model_used': model_type
            }

    return render_template('analyze.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
