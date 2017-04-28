import logging
import requests
from flask import Flask
from flask import request
from flask import Response
from flask import make_response
from functools import wraps
from datetime import datetime
from sklearn.externals import joblib

# Flask was chosen as it's ease of use in prototyping. Ideally, if python was still 
# the language of choice, a library like tornado, or uvloop would be used instead.
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
        
        # I love logging everything if I can. For simplicity I'm just dumping everything to stdout in the container, 
        # and I'm dumping the minimum of information. Ideally I'd dump this into some sort of message queue (sqs maybe?), 
        # as a json object, containing a bit more information. Things like useragent, headers, etc. That way, if 
        # there is an issue, we have a nice chunk of data in the audit trail to look at.
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
        # I'm using just a machine learning classifier to do my filtering, but that could
        # be made more efficient, by adding a few simple manual filters here, that weed out
        # the most obvious sql injection attempts. If the query passes those, then we can
        # use more expensive filtering.
        
        if len(request.args.values()) > 0:
            # vectorize the request arguments values
            # If this was ment to run in the real world, I'd do some sort of de-obfuscation here.
            # Base64 decode, un-url encode any remaining url encoded values, etc. If this was written
            # for a specific application, I could also maybe sanitize these, and strip out 
            # anything that would not be valid input for the upstream app. We could also vary the filtering
            # for specific paths, being more strict on some.
            vectors = vectorizer.transform(request.args.values())

            # Here, I'm using an svm classifier, but that is not likely to be the ideal choice
            # for a production environment. SVM doesn't scale to large data sets well. Most likely
            # I'd imagine something like a random forest classifier would work best; something that
            # could still be done efficiently on cpu.
            for prediction in classifier.predict(vectors):
                status = app.config['CLASSES'][prediction]['status']
                message = app.config['CLASSES'][prediction]['message']

                # So, here if I really wanted to do this well, classification would not be
                # a boolean category. I'd get the probability from the classifier, and then
                # add that to a total score for all query parameters. You could then choose
                # how strict you want your filter to be, by setting a threshold on the score.
                
                # I did not do that here, because that adds complexity to what is supposed to 
                # a simple example. 
                
                # don't do anything with negatives
                if status == 200:
                    continue
                return message, status
        return view(*args, **kwargs)
    return decorated


# Only GET, no post, put, or anything else. 
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
    
    # This here, is probably the most inefficient way to handle this task. I'm storing everything
    # in memory, then passing it on to the client. Ideally I'd stream the response to the client
    # as it arrived from the upstream server. However, all attempts I've made to do that in 
    # Flask in the past have had issues. Flask is just not suited for that task with out jumping
    # through some hoops. So in a production situation, you'd want to use something else, like
    # tornado for example.
    req = requests.get("%s/%s" % (app.config['PROXY_TARGET'], path), params=request.args, headers=request.headers)
    response_content = req.content
    content_type = req.headers.get('content-type', 'text/html')
    status = req.status_code
    
    # There's probably some headers I shouldn't be ignoring from the upstream server, but for now 
    # just setting the content_type works.
    return Response(response_content, content_type=content_type, status=status)


if __name__ == '__main__':
    app.run(threaded=True, host='127.0.0.1', port=8080, debug=True)
