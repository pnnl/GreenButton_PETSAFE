#!/bin/bash

# This script assumes it's being run from within /setup

# Check if MySQL is installed yet; if not, do so
if dpkg -l mysql-server > /dev/null; then
    echo -n "MySQL needs to be installed. Continue? Y/N: "
    read continue
    if [ $continue == "y" || $continue == "Y" || $continue == "yes" ]; then
        sudo apt install mysql-server
    else
        echo "Exiting."
    fi
fi

# Set up database root password
echo -n "Please enter a root password for the database: "
read password
echo "[client]" >> ~/.my.cnf
echo "password=$password" >> ~/.my.cnf
chmod 600 ~/.my.cnf
mysql "ALTER USER root IDENTIFIED BY '$password';"

# Set up MySQL server structure
cd sql
bash init_databases.sh
cd ..
echo "MySQL database setup complete. You may now populate with data."

