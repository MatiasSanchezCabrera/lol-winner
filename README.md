# lol-winner
This is a personal project where I train and expose a model to predict the winner of a League of Legends match before the game starts.

## game_fetcher.py
This file contains the definition of the Fetcher object which searches for matches and saves them into a postgres db. The perpuse of this object is to collect the data for training.

If you wish to use the fetcher, you'll need to get a Riot Games API Key (https://developer.riotgames.com/) and postgres db with the following tables:
***matches_matches***
- match_id (bigint)
- match_detail (json)
- region (varchar(5))

***accounts_accountfetched***
- account_id (bigint)
- timestamp (bigint)
- region (varchar(5))

To initialize a Fetcher, you need to pass the region, the season, the current patch (such as 7.18) and the summoner name of a seed player.