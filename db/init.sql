CREATE DATABASE weather;

CREATE TABLE users
(
    username varchar(50),
    firstname varchar(50),
    lastname varchar(50) not null,
    email varchar(255) not null unique,
    hash varchar(255) not null
);
