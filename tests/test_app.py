import filterproxy
import unittest
import mock


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, content, status_code, headers):
            self.content = content
            self.status_code = status_code
            self.headers = headers

    return MockResponse('OK', 999, {})


class FilterProxyTestCase(unittest.TestCase):

    def setUp(self):
        # Configure the app
        filterproxy.app.config['TESTING'] = True
        filterproxy.app.config['PROXY_TARGET'] = "http://testdomain"
        filterproxy.app.config['PREDICTOR_MODEL'] = "/app/svm_linear_classifier.pkl"
        filterproxy.app.config['VECTORIZOR'] = "/app/vectorizer.pkl"
        filterproxy.app.config['CLASSES'] = {
            'negative': {'message': '', 'status': 200},
            'positive': {'message': '403 Forbidden', 'status': 403},
        }
        self.app = filterproxy.app.test_client()
        # these are test query strings that the app should reject, or accept
        self.test_arguments = [
            ['105 OR 1=1', 403],
            ['hello, world!', 999],
            ['select * from users where username=%s', 403],
            ['Google announces last security update dates for Nexus and Android phones', 999],
            ['" or ""="', 403],
            ['To put it simply, read no further and buy this tape.', 999],
            ['105; DROP TABLE Suppliers', 403],
            ['', 999]
        ]

    @mock.patch('filterproxy.requests.get', side_effect=mocked_requests_get)
    def test_allowed_methods(self, mock_get):
        """
        Verify that only the http get method is allowed

        :param mock_get: mock of requests.get
        """
        self.assertEqual(self.app.post('/').status_code, 405)
        self.assertEqual(self.app.put('/').status_code, 405)
        self.assertEqual(self.app.delete('/').status_code, 405)
        self.assertEqual(self.app.get('/test').status_code, 999)
        mock_get.assert_called_once()
        self.assertEqual(mock_get.call_args[0][0], 'http://testdomain/test')

    @mock.patch('filterproxy.requests.get', side_effect=mocked_requests_get)
    def test_sql_filter(self, mock_get):
        for test_argument, status_code in self.test_arguments:
            response = self.app.get('/', query_string=dict(test=test_argument))
            self.assertEqual(response.status_code, status_code)
        self.assertEqual(mock_get.call_count, 4)

if __name__ == '__main__':
    unittest.main()
