PROXY_TARGET = "http://upstream"
PREDICTOR_MODEL = "/app/svm_linear_classifier.pkl"
VECTORIZOR = "/app/vectorizer.pkl"
CLASSES = {
    'negative': {'message': '', 'status': 200},
    'positive': {'message': '403 Forbidden', 'status': 403},
}
