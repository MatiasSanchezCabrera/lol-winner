# lol-winner
This is a personal project where I train and expose a model to predict the winner of a League of Legends match after champion select.

## game_fetcher.py
This file contains the definition of the Fetcher object which searches for matches and saves them into a postgres db. The purpose of this object is to collect the data for model training.

If you wish to use the Fetcher, you'll need to get a Riot Games API Key (https://developer.riotgames.com/) and a postgres database with the following tables:

***matches_match***
- match_id (bigint)
- match_detail (json)
- region (varchar(5))

***accounts_accountfetched***
- account_id (bigint)
- timestamp (bigint)
- region (varchar(5))

Run db_script.sql to create this tables in your database.

To initialize a Fetcher you need to pass the region, the season, the current patch (such as 7.18) and the summoner name of a seed player.