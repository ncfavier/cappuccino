try:
    import ujson as json
except ImportError:
    import json

import os
import threading

import bottle
import irc3


class UserDB(dict):
    def __init__(self, bot, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot
        if not os.path.exists('data'):
            os.mkdir('data')
            bot.log.debug('Created data/ directory')
        self.file = os.path.join('data', 'ricedb.json')
        with open(self.file, 'r') as fd:
            self.update(json.load(fd))

        try:
            self.config = self.bot.config[__name__]
            if not self.config.get('enable_http_server'):
                return
            host, port = self.config['http_host'], int(self.config['http_port'])
        except KeyError:
            host, port = '127.0.0.1', 8080

        bottle.route('/')(self.http_index)
        bottle_thread = threading.Thread(
            target=bottle.run, kwargs={'quiet': True, 'host': host, 'port': port}, name='ricedb HTTP server')
        bottle_thread.daemon = True
        bottle_thread.start()
        self.bot.log.info('HTTP server started on http://{0}:{1}'.format(host, port))

    def http_index(self):
        bottle.response.content_type = 'application/json'
        return json.dumps(self)

    @irc3.extend
    def get_user_value(self, username, key):
        try:
            return self.get(username)[key]
        except (KeyError, TypeError):
            return None

    @irc3.extend
    def set_user_value(self, username, key, value):
        data = {key: value}
        self[username] = data
        with open(self.file, 'w') as fd:
            json.dump(self, fd)
