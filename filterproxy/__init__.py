import logging
import requests
from flask import Flask
from flask import request
from flask import Response
from flask import make_response
from functools import wraps
from datetime import datetime
from sklearn.externals import joblib

app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler())
app.logger.setLevel(logging.INFO)
app.config.from_envvar('FILTERPROXY_SETTINGS')
classifier = joblib.load(app.config['PREDICTOR_MODEL'])
vectorizer = joblib.load(app.config['VECTORIZOR'])


def log_request(view):
    """
    Logs requests made to the proxy

    :param view: the client requested view
    :return: the client request view
    """
    @wraps(view)
    def decorated(*args, **kwargs):
        resp = make_response(view(*args, **kwargs))
        ip = request.remote_addr
        method = request.method
        timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
        user_agent = request.headers.get('User-Agent', '-')
        request_path = request.full_path
        status = resp.status
        log_string = "%s - [%s] %s: \"%s\" - \"%s\", %s" % (ip, timestamp, method, request_path, user_agent, status)
        app.logger.info(log_string)
        return resp
    return decorated


def dumb_sql_filter(view):
    """
    Filters request arguments for possible sql injection using an svm classifier,
     and returns a custom status code on match

    :param view: the client requested view
    :return: the client request view, or custom status
    """
    @wraps(view)
    def decorated(*args, **kwargs):
        if len(request.args.values()) > 0:
            # vectorize the request arguments values
            vectors = vectorizer.transform(request.args.values())

            # check the predictions
            for prediction in classifier.predict(vectors):
                status = app.config['CLASSES'][prediction]['status']
                message = app.config['CLASSES'][prediction]['message']

                # don't do anything with negatives
                if status == 200:
                    continue
                return message, status
        return view(*args, **kwargs)
    return decorated


@app.route('/', methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
@log_request
@dumb_sql_filter
def root(path="/"):
    """
    Queries the proxied server, and forwards the response

    :param path: client request path
    :return: Response object containing the response from the upstream server
    """
    req = requests.get("%s/%s" % (app.config['PROXY_TARGET'], path), params=request.args, headers=request.headers)
    response_content = req.content
    content_type = req.headers.get('content-type', 'text/html')
    status = req.status_code
    return Response(response_content, content_type=content_type, status=status)


if __name__ == '__main__':
    app.run(threaded=True, host='127.0.0.1', port=8080, debug=True)
