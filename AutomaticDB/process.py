#!/usr/bin/env python3

"""
@author: sylvain,jesse
"""

# Functions to select db layer features within the extent of the S2 image. 
"""
Select features from the database layers that are within the S2 image extent 
"""
from config_connection import config
import ogr
import os
import shutil
import collections
import pprint
import ConstructQuestions
import DatabaseIO as db

from zipfile import ZipFile
import re

from shapely.geometry import box
from shapely.wkt import loads

import rasterio 
from rasterio import windows
from rasterio.warp import calculate_default_transform, reproject, Resampling

from itertools import product

import urllib
import urllib.request

import xml.etree.ElementTree
import numpy as np
import scipy.stats as st
import random

# Download S2 Images from a list of URLs

## Function to handle url/authentication request

def credentials(url, username, password):
    p = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    p.add_password(None, url, username, password)
    handler = urllib.request.HTTPBasicAuthHandler(p)
    opener = urllib.request.build_opener(handler)
    urllib.request.install_opener(opener)


def unzip_and_reproject(zip_name, out_dir, output_crs):
    img_name = None
    with ZipFile(zip_name,'r') as zfile:
        for file in zfile.namelist():
            if file.endswith(".tif"):
                img_name = file
                with zfile.open(img_name) as src:
                    destname = "/tmp/to_reproject.tif"
                    with open(destname, 'wb') as dest:
                        shutil.copyfileobj(src, dest)
                    break
    
    with rasterio.open("/tmp/to_reproject.tif") as src:
        transform, width, height = calculate_default_transform(
           src.crs, output_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'transform': transform,
            'width': width,
            'height': height,
            'driver': 'GTiff',
            'dtype': 'uint8',
            'count': 3,
            'crs' : output_crs
        })
        outpath = os.path.join(out_dir, os.path.basename(img_name))
        with rasterio.open(outpath, 'w',**kwargs) as dst:
            for i in range(1, 4):
                img = rasterio.band(src, i)
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=output_crs,
                    resampling=Resampling.nearest)


# Function to Tile Images and Write to disk
# Inspired by: #285499 - how-to-split-multiband-image-into-image-tiles-using-rasterio

def get_tiles(ds, width=512, height=512):
    ncols, nrows = ds.meta['width'], ds.meta['height']
    offsets = product(range(0, ncols, width), range(0, nrows, height))
    big_window = windows.Window(col_off=0, row_off=0, width=ncols, height=nrows)
    for col_off, row_off in  offsets:
        window = windows.Window(col_off=col_off, row_off=row_off, width=width, height=height).intersection(big_window)
        transform = windows.transform(window, ds.transform)
        yield window, transform
                    
# Function to tile an S2 image                    
def tile(original_dir, img_dir,tile_width=512,tile_height=512):
    print("Listing all registered images")
    imgs = [os.path.join(original_dir, file) for file in os.listdir(original_dir) if file.endswith('.tif')]

    paths = []
    for img in imgs:      
        print("Tiling " + img)
        tile_dir = os.path.splitext(os.path.basename(img))[0]
        
        out_path = os.path.join(img_dir,tile_dir)
        paths.append(out_path)
        
        if not os.path.exists(out_path):
            os.mkdir(out_path)
        
            with rasterio.open(img) as tile:
                meta = tile.meta.copy()
                output_filename = tile_dir + '_{}-{}.tif'
                for window, transform in get_tiles(tile,width=tile_width,height=tile_height):
                    meta['transform'] = transform
                    meta['width'], meta['height'] = window.width, window.height
                    outpath = os.path.join(out_path,output_filename.format(int(window.col_off), int(window.row_off)))
                    if not os.path.exists(outpath):
                        with rasterio.open(outpath, 'w', **meta) as outds:
                            outds.write(tile.read(window=window))
    return paths


#Check that there is something to see on the image
def checkImage(imgName):
    img = rasterio.open(imgName).read()
    if img.shape[1] != 512 or img.shape[2] != 512:
        return False
    mean_value = np.mean(img)
    if mean_value < 30 or mean_value > 225:
        return False
    return True

def selectNTiles(imgNames, N):
    selectedList = []
    iterNum = 0
    random.seed()
    random.shuffle(imgNames)
    while len(selectedList) < N and iterNum < len(imgNames):
        if checkImage(imgNames[iterNum]):
            selectedList.append(imgNames[iterNum])
            print(imgNames[iterNum])
        iterNum += 1
    if len(selectedList) < N:
        print('Warning, could not select enough images')
    return selectedList
        

# Function to Intersect OSM features with Image tiles. 
def GetFeaturesPerImage(layers_list,img_list,main_img):
    
    params = config()
    databaseServer = params['host']
    databaseName = params['database']
    databaseUser = params['user']
    databasePW = params['password']
    connString = "PG: host=%s dbname=%s user=%s password=%s" % (databaseServer,databaseName,databaseUser,databasePW)
    

    
    with rasterio.open(main_img) as src:
        top_left_X, bottom_right_Y,bottom_right_X, top_right_Y = src.bounds
        bboxMainImage = box(top_left_X, bottom_right_Y,bottom_right_X, top_right_Y)
        
    bboxList = []
    featuresList = {}
    for index, img in enumerate(img_list):
        with rasterio.open(img) as src:
            top_left_X, bottom_right_Y,bottom_right_X, top_right_Y = src.bounds
            bboxList.append(box(top_left_X, bottom_right_Y,bottom_right_X, top_right_Y))
            featuresList['%s' %os.path.splitext(os.path.basename(img))[0]] = {}

    
    #Define POSTGRESQL Connection Variables
    conct = ogr.Open(connString)
    for i , layer in enumerate(layers_list):
        print('Working on layer %s' %layer)
        osm_layer = conct.GetLayer(layer)
        for count, feature in enumerate(osm_layer):
            geom = feature.GetGeometryRef()
            feat_geom = geom.ExportToWkt()
            feat = loads(feat_geom)
            if layer == 'import.osm_landusages' and feature.GetField('type') == 'island':
                continue
            to_append = feat
            if layer == 'import.osm_roads' and feature.GetField('class') != 'highway':
                continue
            if layer == 'import.osm_landusages':
                type_land = feature.GetField('type').replace('_', ' ')
                if type_land == 'residential' or type_land == 'grass' or type_land == 'construction'\
                or type_land == 'industrial' or type_land == 'retail' or type_land == 'religious':
                    type_land += ' area'
                to_append = [feat, type_land]
            if layer == 'import.osm_buildings':
                type_building = feature.GetField('type')
                if type_building == 'yes' or type_building == 'house' or type_building == 'apartments' or type_building == 'detached':
                    type_building = 'residential'
                if type_building == 'commercial'\
                or type_building == 'industrial' or type_building == 'retail'\
                or type_building == 'supermarket' or type_building ==  '	warehouse'\
                or type_building == 'kiosk':
                    type_building = 'commercial'
                to_append = [feat, type_building]
            if feat.intersects(bboxMainImage):
                for index, img in enumerate(img_list):
                    if feat.intersects(bboxList[index]):
                        new_feat = feat.intersection(bboxList[index])
                        if type(to_append) == list:
                            to_append[0] = new_feat
                        else:
                            to_append = new_feat
                        if '%s' %layer in featuresList['%s' %os.path.splitext(os.path.basename(img))[0]]:
                            #append the new feature to the existing layer key.
                            featuresList['%s' %os.path.splitext(os.path.basename(img))[0]]['%s' %layer].append(to_append)
                        else:
                             # create a new item for layer key
                            featuresList['%s' %os.path.splitext(os.path.basename(img))[0]]['%s' %layer] = [to_append]
        print(featuresList)
    return featuresList
 
if __name__ == "__main__":
    
    # Filepaths
    zipDir = r"./USGS_Zips/"
    tileDir = r"./USGS_OriginalTiles/"
    img_path = 'USGS_Tiles/'
    output_crs = 'EPSG:3857'
    
    # Split S2 images into 
    tile_width,tile_height = 512,512
    tile_paths = tile(tileDir, img_path,tile_width,tile_height)
    
    db.write_to_db()
    if db.get_id_from_key("people", "login", "AutoDB") == []:
        db.add_people('AutoDB', '', 'Automatic DB creation', '')

    to_exclude = ['l_11340226_06_04800_col_2007', '217622', '242620', '260640', '235585', '29834280', '29263680', '28962700']
    for i, tile_path in enumerate(tile_paths):
        if db.get_id_from_startkey("images", "original_name", os.path.basename(tile_path)) == [] and os.path.basename(tile_path) not in to_exclude:
            print("Image #" + str(i) + "/" + str(len(tile_paths)) + ": " + tile_path)
            img_files = [os.path.join(tile_path, file) for file in os.listdir(tile_path) if file.endswith('.tif')]
            layers = ['import.osm_waterareas','import.osm_roads','import.osm_buildings','import.osm_landusages']
            tiles = selectNTiles(img_files, 100)
            if (tiles == []):
                continue
            features_by_img = GetFeaturesPerImage(layers,tiles,os.path.join(tileDir,os.path.basename(tile_path)+'.tif'))
            np.save('/tmp/feat', features_by_img)
            number_images = 0
            for feature in features_by_img:
                if len(features_by_img[feature]) < 2:
                    continue
                if number_images < 100:
                    number_images += 1
                    with rasterio.open(os.path.join(tile_path, feature + '.tif')) as src:
                        top_left_X, top_left_Y, _, _ = src.bounds
                    QuestionBuilder = ConstructQuestions.ConstructImageQuestion(features_by_img[feature])
                    QuestionBuilder.chooseQuestionsToAsk(100)
                    QuestionBuilder.writeInDB(os.path.join(img_path,os.path.basename(tile_path), feature+'.tif'), top_left_X, top_left_Y)
        
            db.write_to_db()
