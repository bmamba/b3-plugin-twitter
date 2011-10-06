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
# Changelog:
#
# 08/08/2011 - 1.0 - BlackMamba
# - initial version
# 01/09/2011 - 1.1 - BlackMamba
# - print tweets of a twitter account ingame
# - print expiration time of a ban
# - print admin name who banned the player
# - now compatible with b3 v1.7.x
#

__author__  = 'BlackMamba'
__version__ = '1.1'


import b3, b3.events, b3.plugin
import twitter
import re
import datetime, time

class Tweet:
	text = ""
	id = 0
	time = ""

class Tweets:
	tweets = None
	current = None
	newest = None
	api = None
	max = None
	debug = None
	user = None

	def __init__(self, debug, api, user):
		self.tweets = []
		self.current = 0
		self.newest = 0
		self.max = 5
		self.debug = debug
		self.api = api
		self.user = user

	def getNext(self):
		try:
			tweet = self.tweets[self.current]
		except:
			current = 0
			return None

		self.current += 1
		if self.current >= len(self.tweets) or self.current >= self.max:
			self.current = 0
		return tweet

	def put(self,tweet):
		self.tweets.append(tweet)
		self.debug('adding %s' % tweet.text)
		if tweet.id > self.newest:
			self.newest = tweet.id
			current = 0

	def clear(self):
		self.tweets = []

	def reload(self):
		tweets = self.api.GetUserTimeline(self.user)
		for t in tweets:
			tweet = Tweet()
			tweet.id = t.id
			tweet.text = t.text
			st = time.strptime(t.created_at,"%a %b %d %H:%M:%S +0000 %Y")
			dt = datetime.datetime(st[0], st[1], st[2], st[3], st[4], st[5])
			offset = time.altzone
			dt = dt + datetime.timedelta(seconds=-1*offset)
			tweet.time = str(dt)
			self.put(tweet)
		

class B3TwitterPlugin(b3.plugin.Plugin):

	_twitterlevel = 100

	_tweetonkick = False
	_tweetonbantemp = False
	_tweetonban = False

	_tweetAdmin = False
	_tweetDate = True

	_consumer_key = None
	_consumer_secret = None
	_access_token = None
	_access_token_secret = None

	_showtweetsminutes = 5
	_showtweetsenabled = False
	_showtweetsmax = 5
	_showtweetsuser = None
	
	_twitterapi = None
 	_reColor = re.compile(r'(\^[0-9a-z])')

	_cronTab = None
	_cronTab2 = None
	_tweets = None
  
	def onLoadConfig(self):
		self._consumer_key = self.config.get('authentication','consumer_key')
		self._consumer_secret = self.config.get('authentication','consumer_secret')
		self._access_token = self.config.get('authentication','access_token')
		self._access_token_secret = self.config.get('authentication','access_token_secret')

		self._tweetonkick = self.config.getboolean('tweet','tweetonkick')
		self._tweetonbantemp = self.config.getboolean('tweet','tweetonbantemp')
		self._tweetonban = self.config.getboolean('tweet','tweetonban')

		self._tweetAdmin = self.config.getboolean('tweet','tweetadminname')
		self._tweetDate = self.config.getboolean('tweet','tweetexpirationdate')

		self._showtweetsminutes = self.config.getint('showtweets','nexttweet')
		self._showtweetsenabled = self.config.getboolean('showtweets','enabled')
		self._showtweetsmax = self.config.getint('showtweets','maxtweets')
		self._showtweetsreload = self.config.getint('showtweets','updatetweets')
		self._showtweetsuser = self.config.get('showtweets','user')

		self._twitterlevel =  self.config.getint('commands','twitterlevel')


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

		if self._showtweetsenabled and int(self._showtweetsminutes) >= 1 and self._showtweetsuser != None:
			self._tweets = Tweets(self.debug, self._twitterapi, self._showtweetsuser)
			self._tweets.reload()

			if self._cronTab:
				self.console.cron - self._cronTab

			self._cronTab = b3.cron.PluginCronTab(self, self.showtweets, minute='*/%i' % int(self._showtweetsminutes))
			self.console.cron + self._cronTab
			self.debug('Showing tweets ingame enabled')

			if int(self._showtweetsreload) >= 1:
				if self._cronTab2:
					self.console.cron - self._cronTab2

				self._cronTab2 = b3.cron.PluginCronTab(self, self.reload_tweets, minute='*/%i' % int(self._showtweetsreload))
				self.console.cron + self._cronTab2
				self.debug('Reloading tweets every %i minutes enabled' % int(self._showtweetsreload))

	def removeColors(self, text):
		return re.sub(self._reColor, '', text).strip()

	def startup(self):
		"""\
		Initialize plugin settings
		"""
		

	def onEvent(self, event):
		"""\
		Handle intercepted events
		"""
		if not event.client or event.client.cid == None or len(event.data) <= 0:
			return

		action = ''

		if event.type == b3.events.EVT_CLIENT_KICK:
			action = 'kicked'
			p = event.client.lastKick

		if event.type == b3.events.EVT_CLIENT_BAN_TEMP:
			action = 'banned'
			p = event.client.lastBan

		if event.type == b3.events.EVT_CLIENT_BAN:
			action = 'banned'
			p = event.client.lastBan

		if p == None:
			return
		#old ban/kick
		if time.time() - p.timeAdd > 60:
			self.debug('I dont tweet this ban since it seems to be an old ban (older than %i seconds)' % (time.time() - p.timeAdd))
			return
		clientName = self.removeColors(event.client.name);
		text = 'Bot:'
		if self._tweetAdmin:
			admin = b3.clients.getByCID(p.adminId)
			text = '%s %s %s %s' % (text, self.removeColors(admin.name), action, clientName)
		else:
			text = '%s %s was %s' % (text, clientName, action)
		if self._tweetDate and (p.type == 'Ban' or p.type == 'TempBan') :
			dt = datetime.datetime.fromtimestamp(p.timeExpire)
			if p.timeExpire == -1:
				date = 'permanently'
			else:
				date = 'until %s' % (dt.strftime('%d/%m/%Y, %H:%M'))
			text = '%s %s' % (text, date)
		text = '%s: %s' % (text, self.removeColors(p.reason))
		text = text[0:139]
		self.debug('Tweet: %s' % text)
		self._twitterapi.PostUpdate('%s' % text)

		status = self._twitterapi.PostUpdate('%s' % rmColor)

	def cmd_twitter(self, data, client, cmd=None):
		self.debug('Tweet: %s' % data)
		self._twitterapi.PostUpdate('%s: %s' % (client.name, data))

	def showtweets(self):
		tweet = self._tweets.getNext()
		if tweet:
			self.console.say('@%s tweets: %s (%s)' % (self._showtweetsuser, tweet.text, tweet.time))
			self.debug('@%s tweets: %s (%s)' % (self._showtweetsuser, tweet.text, tweet.time))

	def reload_tweets(self):
		self.debug('Reloading tweets')
		self._tweets.reload()

