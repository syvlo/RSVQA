Build POSTGRESQL database
- @author: jesse
- date: August 29, 2018


Use the following steps to setup a POSTGRESQL database and populate it with OSM data.
 
1. Build postgresql db and populate with osm data
 - Create user: 
  > createuser --no-superuser --no-createrole --createdb [username]
  
 - Create db: 
  > createdb -E UTF-8 -l en_US.UTF-8 -O [username] [dbname]
  
 - Enable the PostGIS and Hstore extensions for this database: 
  > install postgresql, postgis
  > psql [dbname] -c "create extension postgis;" ##Must be done everytime a db is created or import will fail. 
  > psql [dbname] -c "create extension hstore;"

2. Install Imposm
 - Create go variables for imposm installation path
 > export GOPATH="$HOME/go"
 > export PATH="$GOPATH/bin:$PATH"
   

3. Download imposm binary
 - Start a new terminal ensure variables are initialized and run:
 > brew install leveldb
 > go get github.com/omniscale/imposm3
 > go install github.com/omniscale/imposm3/cmd/imposm
 > imposm version  # to confirm install was successfull

4. Configure imposm
 - Create a data dir for the db on the server

 - Define config.json in data dir as:

 {
    "cachedir": "[path to data dir]/data/imposm3_cache",
    "connection": "postgis://username:password@localhost:port/database",
    "mapping": "[path to db data dir]/data/mapping.yml"
 }

 - Save mapping.yml to /data dir to define db schema. 
 --See link for default mapping: https://raw.githubusercontent.com/omniscale/imposm3/master/example-mapping.yml 

5. Import osm data to postgresql db:
 - Move to db data dir: 
 > cd ~/data
 - Read osm data and push into db tables: 
 > imposm import -config config.json -read [target.osm.pbf file] -write -optimize -overwritecache -diff

 - Push tables to production schema: 
 > imposm import -config config.json -deployproduction

