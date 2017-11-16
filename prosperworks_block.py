from nio import GeneratorBlock
from nio.signal.base import Signal
from nio.properties import IntProperty, StringProperty, ObjectProperty, \
    PropertyHolder, VersionProperty, BoolProperty
from nio.modules.web import RESTHandler, WebEngine
import requests


class BuildSignal(RESTHandler):

    def __init__(self, endpoint, notify_signals, logger):
        super().__init__('/'+endpoint)
        self.notify_signals = notify_signals
        self.logger = logger

    def before_handler(self, req, rsp):
        # Overridden in order to skip the authentication in the framework
        return

    def on_post(self, req, rsp):
        body = req.get_body()
        if not isinstance(body, dict):
            self.logger.error("Invalid JSON in body: {}".format(body))
            return
        self.notify_signals([Signal(body)])


class WebServer(PropertyHolder):

    host = StringProperty(title='Host', default='0.0.0.0')
    port = IntProperty(title='Port', default=8182)
    endpoint = StringProperty(title='Endpoint', default='')


class Prosperworks(GeneratorBlock):

    version = VersionProperty("1.0.0")
    web_server = ObjectProperty(
        WebServer, title='Web Server', default=WebServer())
    callback_url = StringProperty(
        title="Callback URL",
        default="",
        allow_none=False)
    access_token = StringProperty(
        title="Access Token",
        default="[[PROSPERWORKS_ACCESS_TOKEN]]",
        allow_none=False)
    email = StringProperty(
        title="Prosperworks Email Address",
        default="Rev.Dev@n.io",
        allow_none=False)
    event = StringProperty(title='Event', default='new', allow_none=False)
    event_type = StringProperty(title='Type', default='lead', allow_none=False)

    def __init__(self):
        super().__init__()
        self._server = None
        self._subscription_id = None

    def configure(self, context):
        super().configure(context)
        self._create_web_server()
        response = self._request('post', body={
                "target": self.callback_url(),
                "type": self.event_type(),
                "event": self.event()
            })
        print('$$$$$$$$')
        print(response.status_code)
        print('$$$$$$$$')
        if response.status_code != 200:
            raise Exception
        self._subscription_id = response.json()["id"]

    def start(self):
        super().start()
        self._server.start()

    def stop(self):
        self._request('delete', id=self._subscription_id)
        self._server.stop()
        super().stop()

    def _create_web_server(self):
        self._server = WebEngine.add_server(
            self.web_server().port(), self.web_server().host())
        self._server.add_handler(
            BuildSignal(
                self.web_server().endpoint(),
                self.notify_signals,
                self.logger,
            )
        )

    def _request(self, method='post', id=None, body=None):
        url = 'https://api.prosperworks.com/developer_api/v1/webhooks'
        if id:
            url += "/{}".format(id)
        kwargs = {}
        kwargs['headers'] = {
            "Content-Type": "application/json",
            "x-pw-accesstoken": self.access_token(),
            "x-pw-application": "developer_api",
            "x-pw-useremail": self.email()
        }
        if body:
            kwargs['json'] = body
        response = getattr(requests, method)(url, **kwargs)
        print('@@@@@')
        print(response.status_code)
        print('@@@@@')
        if response.status_code != 200:
            self.logger.error("Http request failed: {} {}".format(
                response, response.json()))
        self.logger.debug("Http response: {}".format(response.json()))
        return response
