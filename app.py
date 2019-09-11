from flask import Flask, request, Response

from habraproxy import process_proxy

app = Flask(__name__)


@app.route("/<path:path>", methods=['GET'])
def main(path: str) -> Response:
    app.logger.debug('processing proxy for {}'.format(path))
    return process_proxy(request)
