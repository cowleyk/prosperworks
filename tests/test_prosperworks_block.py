import json
from unittest.mock import MagicMock, patch

import responses

from nio.testing.block_test_case import NIOBlockTestCase
from ..prosperworks_block import Prosperworks, BuildSignal


class TestBuildSignal(NIOBlockTestCase):

    def test_web_handler_post_dict(self):
        notify_signals = MagicMock()
        handler = BuildSignal(endpoint='',
                              notify_signals=notify_signals,
                              logger=MagicMock())
        request = MagicMock()
        request.get_body.return_value = {"I'm a": "dictionary"}
        handler.on_post(request, MagicMock())
        self.assertDictEqual(
            notify_signals.call_args[0][0][0].to_dict(),
            {"I'm a": "dictionary"})


class TestProsperworks(NIOBlockTestCase):

    @responses.activate
    def test_block_propertes_are_passed_to_web_engine_and_handler(self):
        blk = Prosperworks()
        responses.add(
            responses.POST,
            'https://api.prosperworks.com/developer_api/v1/webhooks',
            json={"id": "id"},
        )
        module = Prosperworks.__module__
        with patch("{}.WebEngine".format(module)) as engine:
            with patch("{}.BuildSignal".format(module)) as handler:
                self.configure_block(blk, {})
                engine.add_server.assert_called_once_with(
                    blk.web_server().port(),
                    blk.web_server().host(),
                )
                handler.assert_called_once_with(
                    blk.web_server().endpoint(),
                    blk.notify_signals,
                    blk.logger,
                )

    @responses.activate
    def test_subscriptions_are_created_and_destroyed(self):
        blk = Prosperworks()
        callback_url = "callback"
        responses.add(
            responses.POST,
            'https://api.prosperworks.com/developer_api/v1/webhooks',
            json={"id": "id"},
        )
        responses.add(
            responses.DELETE,
            'https://api.prosperworks.com/developer_api/v1/webhooks/id',
            json={"id": "id"},
        )
        module = Prosperworks.__module__
        with patch("{}.WebEngine".format(module)):
            with patch("{}.BuildSignal".format(module)):
                self.configure_block(blk, {
                    "callback_url": callback_url,
                    "subscription": [{
                        "event": "event1",
                        "type": "type1"
                    },
                    {
                        "event": "event2",
                        "type": "type2"
                    }]
                })
        self.assertEqual(len(responses.calls), 2)
        self.assertDictEqual(
            json.loads(responses.calls[0].request.body.decode()), {
                "target": callback_url,
                "type": "type1",
                "event": "event1",
            }
        )
        self.assertDictEqual(
            json.loads(responses.calls[1].request.body.decode()), {
                "target": callback_url,
                "type": "type2",
                "event": "event2",
            }
        )
        headers = responses.calls[0].request.headers
        self._assert_header_value(headers, "Content-Type", "application/json")
        self._assert_header_value(
            headers, "x-pw-accesstoken", blk.access_token())
        self._assert_header_value(headers, "x-pw-application", "developer_api")
        blk.stop()
        self.assertEqual(len(responses.calls), 4)

    def _assert_header_value(self, headers, header, value):
        self.assertEqual(headers[header], value)