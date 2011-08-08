#
# Plugin Twitter (www.bmamba.de)
# By BlackMamba
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

__author__  = 'BlackMamba'
__version__ = '1.0'


import b3, b3.events, b3.plugin
import twitter
import re

class B3TwitterPlugin(b3.plugin.Plugin):

	_twitterlevel = 100

	_tweetonkick = False
	_tweetonbantemp = False
	_tweetonban = False

	_consumer_key = None
	_consumer_secret = None
	_access_token = None
	_access_token_secret = None
	
	_twitterapi = None
 	_reColor = re.compile(r'(\^[0-9a-z])')
  
	def onLoadConfig(self):
		self._consumer_key = self.config.get('authentication','consumer_key')
		self._consumer_secret = self.config.get('authentication','consumer_secret')
		self._access_token = self.config.get('authentication','access_token')
		self._access_token_secret = self.config.get('authentication','access_token_secret')

		self._tweetonkick = self.config.getboolean('tweet','tweetonkick')
		self._tweetonbantemp = self.config.getboolean('tweet','tweetonbantemp')
		self._tweetonban = self.config.getboolean('tweet','tweetonban')

		self._twitterlevel =  self.config.getint('commands','twitterlevel')

	def removeColors(self, text):
		return re.sub(self._reColor, '', text).strip()

	def startup(self):
		"""\
		Initialize plugin settings
		"""
		self._adminPlugin = self.console.getPlugin('admin') 
		# Initialize Twitter Connection
		self._twitterapi = twitter.Api(consumer_key=self._consumer_key, consumer_secret=self._consumer_secret, access_token_key=self._access_token, access_token_secret=self._access_token_secret)
	
		# listen for client events
		if self._tweetonkick:
			self.registerEvent(b3.events.EVT_CLIENT_KICK)
		if self._tweetonbantemp:
			self.registerEvent(b3.events.EVT_CLIENT_BAN_TEMP)
		if self._tweetonban:
			self.registerEvent(b3.events.EVT_CLIENT_BAN)

		self._adminPlugin.registerCommand(self, 'twitter', self._twitterlevel, self.cmd_twitter)

	def onEvent(self, event):
		"""\
		Handle intercepted events
		"""
		if not event.client or event.client.cid == None or len(event.data) <= 0:
			return

		data = 'Bot: %s' % event.client.name

		if event.type == b3.events.EVT_CLIENT_KICK:
			data = '%s was kicked' % data

		if event.type == b3.events.EVT_CLIENT_BAN_TEMP:
			data = '%s was banned' % data

		if event.type == b3.events.EVT_CLIENT_BAN:
			data = '%s was banned' % data

		if event.data != None:
			if event.data != '':
				data = '%s: %s' % (data, event.data)

		rmColor = self.removeColors(data)

		self.debug('Tweet: %s' % rmColor)
		status = self._twitterapi.PostUpdate('%s' % rmColor)

	def cmd_twitter(self, data, client, cmd=None):
		self.debug('Tweet: $s' % data)
		self._twitterapi.PostUpdate('%s' % data)
