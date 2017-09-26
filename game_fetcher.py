# -*- coding: utf-8 -*-
import time
import requests
import sqlalchemy

class Fetcher(object):

	headers = {"X-Riot-Token": '<YOUR API KEY HERE>'}
	regional_endpoint = {	'BR': 	'br1.api.riotgames.com',
							'EUNE': 'eun1.api.riotgames.com',
							'EUW': 	'euw1.api.riotgames.com',
							'JP': 	'p1.api.riotgames.com',
							'KR': 	'kr.api.riotgames.com',
							'LAN': 	'la1.api.riotgames.com',
							'LAS': 	'la2.api.riotgames.com',
							'NA': 	'na1.api.riotgames.com',
							'OCE': 	'oc1.api.riotgames.com',
							'TR': 	'tr1.api.riotgames.com',
							'RU': 	'ru.api.riotgames.com',
							'PBE': 	'pbe1.api.riotgames.com'	}

	def create_db_engine(self):
		conn = 'postgresql://{}:{}@{}:{}/{}'.format('db_user', 'db_user_pw', 'db_host', 'db_port', 'db_name') # user, password, host, port, db
		return sqlalchemy.create_engine(conn)

	def __init__(self, region, current_season, current_patch, seed):
		self.region = region
		self.current_season = current_season
		self.current_patch = current_patch
		self.db_engine = self.create_db_engine()
		self.seed = seed
		self.summoner_by_name = 'https://{}/lol/summoner/v3/summoners/by-name/'.format(self.regional_endpoint[region])
		self.recent_games = 'https://{}/lol/match/v3/matchlists/by-account/'.format(self.regional_endpoint[region])
		self.match_detail = 'https://{}/lol/match/v3/matches/'.format(self.regional_endpoint[region])
		self.season_filter = '?season=' + str(self.current_season)


	def get_seed_account(self):
	    result = requests.get(self.summoner_by_name + self.seed, headers=self.headers)
	    time.sleep(0.84) # Sleep due to rate limit on api key (100 requests each 120 seconds)
	    self.get_matches_for_account(result.json()['accountId'])

	def get_fellow_accounts(self, accounts):
	    for account in accounts:
	        self.get_matches_for_account(account)

	def get_matches_for_account(self, account_id):
	    result = requests.get(self.recent_games + str(account_id) + self.season_filter, headers=self.headers)    
	    time.sleep(0.84) # Sleep due to rate limit on api key (100 requests each 120 seconds)
	    if result.status_code in [200]:
	    	print 'Matches for account {}'.format(account_id)
		    matches = result.json()
		    self.save_account_fetched(account_id, matches)
		    self.get_match_detail(matches, self.get_fetched_matches())	    	
	    else:		    
		    print 'Banned {}'.format(account_id)
	    	self.save_account_banned(account_id)

	def get_match_detail(self, matches, banned_matches):
		try:
		    for match in matches['matches']:
		        if match['gameId'] not in banned_matches:
		            result = requests.get(self.match_detail + str(match['gameId']), headers=self.headers)
		            time.sleep(0.84) # Sleep due to rate limit on api key (100 requests each 120 seconds)
		            if result.json()['gameVersion'][:len(self.current_patch)] not in [self.current_patch]: return
		            self.save_match_detail(match['gameId'], result.content.replace('\'','"'))
		except (KeyError, IndexError) as e:
			pass
		return

	def save_account_banned(self, account_id):
	    query = "insert into accounts_accountfetched values ({},{},'{}')".format(account_id, str(-1), self.region)
	    self.db_engine.engine.execute(query)

	def save_account_fetched(self, account_id, matches):
	    try:
	    	timestamp = matches['matches'][0]['timestamp']
	    except (KeyError, IndexError) as e:
	    	timestamp = 0
	    query = "insert into accounts_accountfetched values ({},{},'{}')".format(account_id, timestamp, self.region)
	    self.db_engine.engine.execute(query)

	def save_match_detail(self, match_id, detail):
		query = "insert into matches_match values ({},'{}','{}')".format(match_id, detail, self.region)
		self.db_engine.engine.execute(query)		

	def get_fetched_matches(self):
	    query = "select distinct match_id from matches_match where region in ('{}')".format(self.region)
	    return [r for r, in self.db_engine.engine.execute(query)]

	def get_new_accounts(self):
	    query = """
	            select distinct q.account_id
	            from (select distinct json_array_elements((match_detail->'participantIdentities'))->'player'->>'accountId' account_id
	                  from matches_match
	                  where region in ('{}')) q
	            where q.account_id::bigint not in (select distinct account_id from accounts_accountfetched)
	              and q.account_id::bigint not in (0)
	            """.format(self.region)
	    return [r for r, in self.db_engine.engine.execute(query)]

	def fetch(self):
	    accounts = self.get_new_accounts()
	    if not accounts:
	        self.get_seed_account()
	    else:
	    	self.get_fellow_accounts(accounts)
	    self.fetch()