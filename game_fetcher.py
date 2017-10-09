# -*- coding: utf-8 -*-
import sqlalchemy
import json
from riotwatcher import RiotWatcher
from requests import HTTPError

class Fetcher(object):

	def create_db_engine(self):
		conn = 'postgresql://{}:{}@{}:{}/{}'.format('<db_user>', '<db_user_ps>', '<db_host>', '<db_port>', '<db_name>') # user, password, host, port, db
		return sqlalchemy.create_engine(conn)

	def __init__(self, region, season=9, patch=False, seed=''):
		self.watcher = RiotWatcher('<YOUR_API_KEY>')
		self.db_engine = self.create_db_engine()
		self.region = region
		self.season = season
		if not patch:
			self.patch = self.watcher.static_data.versions(region=self.region)[0]
		else :
			self.patch = patch
		self.seed = seed
		self.accepted_queues = [400, 410, 420, 430, 440]

	def get_seed_account(self):
		self.get_matches_for_account(self.watcher.summoner.by_name(region=self.region, summoner_name=self.seed)['accountId'])

	def get_fellow_accounts(self, accounts):
		for account_id in accounts:
			self.get_matches_for_account(account_id)

	def get_matches_for_account(self, account_id):
		try:
			matches = self.watcher.match.matchlist_by_account(region=self.region, account_id=account_id, season=self.season, queue=self.accepted_queues)
			print 'Matches for account {}'.format(account_id)
			self.save_account_fetched(account_id, matches)
			self.get_match_detail(matches, self.get_fetched_matches())
		except HTTPError as e:
			if e.response.status_code == 404:
				print 'No matches found for account {}'.format(account_id)
				self.save_account(account_id, -1)
			else:
				print 'HTTPError with status code {}'.format(e.response.status_code)

	def get_match_detail(self, matches, fetched_matches):
		for match in matches['matches']:
			if match['gameId'] not in fetched_matches:
				detail = self.watcher.match.by_id(region=self.region, match_id=match['gameId'])
				try:
					if float(detail['gameVersion'][:len(self.patch)]) < float(self.patch):
						return
				except ValueError:
					return
				if detail['queueId'] in self.accepted_queues:
					self.save_match_detail(detail['gameId'], json.dumps(detail))

	def save_account(self, account_id, timestamp):
		try:
			query = "insert into accounts_accountfetched values ({},{},'{}')".format(account_id, timestamp, self.region)
			self.db_engine.engine.execute(query)
		except sqlalchemy.exc.IntegrityError:
			pass

	def save_account_fetched(self, account_id, matches):
		try:
			timestamp = matches['matches'][0]['timestamp']
		except (KeyError, IndexError) as e:
			timestamp = 0
		self.save_account(account_id, timestamp)

	def save_match_detail(self, match_id, detail):
		query = "insert into matches_match values ({},'{}','{}')".format(match_id, detail, self.region)
		self.db_engine.engine.execute(query)

	def get_fetched_matches(self):
		query = "select distinct match_id from matches_match where region in ('{}')".format(self.region)
		return [int(r) for r, in self.db_engine.engine.execute(query)]

	def get_new_accounts(self):
		query = """
				select distinct q.account_id
				from (select distinct json_array_elements((match_detail->'participantIdentities'))->'player'->>'accountId' account_id
					from matches_match
					where region in ('{}')) q
				where q.account_id::bigint not in (select distinct account_id from accounts_accountfetched where region in ('{}'))
					and q.account_id::bigint not in (0)
				""".format(self.region, self.region)
		return [r for r, in self.db_engine.engine.execute(query)]

	def fetch(self):
		accounts = self.get_new_accounts()
		if not accounts:
			self.get_seed_account()
		else:
			self.get_fellow_accounts(accounts)
		self.fetch()