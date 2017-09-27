CREATE TABLE accounts_accountfetched
(
    account_id BIGINT NOT NULL,
    timestamp BIGINT,
    region VARCHAR(5)
);
CREATE UNIQUE INDEX accounts_accountfetched_account_id_region_pk ON accounts_accountfetched (account_id, region);
CREATE TABLE matches_match
(
    match_id BIGINT PRIMARY KEY NOT NULL,
    match_detail JSON,
    region VARCHAR(5)
);
CREATE UNIQUE INDEX matches_match_match_id_uindex ON matches_match (match_id);