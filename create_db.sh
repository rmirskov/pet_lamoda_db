#!/bin/bash
sudo -u postgres psql
CREATE USER lamoda_admin WITH PASSWORD 'lamodA2023';
CREATE DATABASE lamoda_db WITH OWNER lamoda_admin;
GRANT ALL PRIVILEGES ON DATABASE lamoda_db to lamoda_admin;
\q
psql -U lamoda lamoda_db
\i lamoda_db.sql
