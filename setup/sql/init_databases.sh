#!/usr/bin/env bash
#
#
#    Copyright (c) 2018-2021 Green Button Alliance, Inc.
#
#    Portions (c) 2013-2018 EnergyOS.org
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
#

# This script will initialize the databases
# it will first delete datacustodian and thirdparty databases
# then it creates them
# then establishes all the tables
# then populates tables with initial data
#
# Copy the appropriate version of prepopulatesql_<dc or tp>_<host><port>.sql to prepopulatesql.sql for your installation

# The user to connect with
user="root"
# Get the SQL password from environment variables
# to avoid storing a secret in a repository
pass=${SQL_PASS}

# drop/create databases 
mysql --user=${user} --defaults-file=~/.my.cnf < cleandatabases_dc.sql
mysql --user=${user} --defaults-file=~/.my.cnf < cleandatabases_tp.sql

# create tables 
mysql --user=${user} --defaults-file=~/.my.cnf < ./thirdparty.sql
mysql --user=${user} --defaults-file=~/.my.cnf < ./datacustodian.sql
#mysql --user=${user} --defaults-file=~/.my.cnf < tokenstore.sql

# prepopulate tables
mysql --user=${user} --defaults-file=~/.my.cnf < populate_dc_sample_data.sql
#mysql --user=${user} --defaults-file=~/.my.cnf < prepopulatesql_users_dc.sql
mysql --user=${user} --defaults-file=~/.my.cnf < prepopulatesql_users_tp.sql
#mysql --user=${user} --defaults-file=~/.my.cnf < prepopulatesql_dc.sql
mysql --user=${user} --defaults-file=~/.my.cnf < prepopulatesql_tp.sql