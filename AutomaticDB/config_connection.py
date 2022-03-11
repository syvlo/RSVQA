#!/usr/bin/python
# Initialisation de la connexion à la base PostgreSQL
from configparser import ConfigParser


def config(filename='vqa_database.ini', section='postgresql'):
    """Parse database connection parameters from ini file and write to dictionary
       --Args:
         - filename: Define file location of the configuration ini file
         - section: Define the section of the ini file to pull config params from. 
           - 'postgresql' defines the postgresql config params
           - 'sentinel_portal' defines logon params for the sentinel portal
       --Returns:
         - Dictionary of connection params.
    """
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)
 
    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
 
    return db
