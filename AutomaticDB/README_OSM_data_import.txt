Build POSTGRESQL database
- @author: jesse
- date: October 12, 2018


Use the following steps to populate the MMRS OSM postgresql DB with OSM data.
 
1. Log on to the MMRS server 'OSM' postgresql DB to verify the rsvqa_user account is established
  > psql  OSM; 
  > type '\wu' to display user names. 
  > type '\q' to exit the DB. 

2. Setup Table Schema and Configuration for the DB tables

 - Create a data dir for the db on the server
   e.g. /stratch/users/[user_name]/[db_name]/data

 - The MMRS postgresql DB name is: OSM
 - The generic user for the DB is User_Name: rsvqa_user, Password: rsvqa.

 - The connection string to be entered in the config.json file is then:

    "postgis://[User_Name]:[Password]@guanabana:5432/[db_name]"

 - The config file 'config.json' should be saved in ./data as:

 {
    "cachedir": "[path to data dir]/data/imposm3_cache",
    "connection": "postgis://rsvqa_user:rsvqa@guanabana:5432/OSM",
    "mapping": "[path to db data dir]/data/mapping.yml"
 }

 - Save mapping.yml saved in the git repository to ./data dir to define db schema. 

 --See link for default mapping: https://raw.githubusercontent.com/omniscale/imposm3/master/example-mapping.yml 

5. Import osm data to postgresql db with imposm:
 - Move to db data dir: 
 > cd ~/data
 - Read osm data and push into db tables with the following command: 
 > /opt/imposm/3/imposm3 import -config config.json -read [target.osm.pbf file] -write -optimize -overwritecache -diff

 - Run the following to push tables to production schema: 
 > imposm import -config config.json -deployproduction

6. Drop the tables in the database and overwrite with new OSM data
   - The MMRS 'OSM' postgresql database has a generic user 'rsvqa_user' and password        	'rsvqa' established on the host 'guanabana'. These parameters are stored in the 	'vqa_config.ini' file with database and sentinel portal logon credentials:

	[postgresql]
	host=localhost
	database=OSM
	user=rsvqa_user
	password=rsvqa
	[sentinel_portal]
	user=[logon name]
	password=[logon password]

   > These credentials are parsed and pulled into function by the config_connection   		function
   > run 'drop_postgres_db_tables.py' which calls config_connection to drop all tables that were created by the 'rsvqa_user'. 

