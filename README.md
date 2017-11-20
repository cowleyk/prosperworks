Prosperworks
============
Block to establish a webhook and forward along incoming signals from a Prosperworks account.

Properties
----------
- **access_token**: API Access token from Prosperworks.
- **callback_url**: URL Prosperworks should send events to, must use `https`.
- **email**: Email address associated with Prosperworks account.
- **subscription**: Event and type of event the webhook should listen for.
- **web_server**: Server configurations that webhook will be running on.

Inputs
------
None

Outputs
-------
- **default**: Events sent from Prosperworks as a nio signal.

Commands
--------
None

Dependencies
------------
None
