import os
import json


class FakeResponse(object):
    status_code = 200
    text = None
    headers = []

    def __init__(self, text):
        self.text = text

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        pass


def response(name):
    content = open(os.path.join(os.path.dirname(__file__), 'responses', name)).read()
    return FakeResponse(content)
