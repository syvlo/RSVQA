#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ensemble de fonctions pour intéragir avec la base de données

import json
import time
import config_S2 as config
import os
from PIL import Image

db_files = {"images": config.images_file, "questions": config.questions_file, "answers": config.answers_file, "people": config.people_file}

class DatabaseException(Exception):
    pass

try:
    with open(config.images_file) as f:
        data_images = json.load(f)
except:
    print('File ' + config.images_file + ' does not exists. Creating it...')
    data_images = {"images": []}
    
try:
    with open(config.people_file) as f:
        data_people = json.load(f)
except:
    print('File ' + config.people_file + ' does not exists. Creating it...')
    data_people = {"people": []}
    
try:
    with open(config.questions_file) as f:
        data_questions = json.load(f)
except:
    print('File ' + config.questions_file + ' does not exists. Creating it...')
    data_questions = {"questions": []}
    
try:
    with open(config.answers_file) as f:
        data_answers = json.load(f)
except:
    print('File ' + config.answers_file + ' does not exists. Creating it...')
    data_answers = {"answers": []}
    
def write_to_db():
    try:
        with open(config.images_file, 'w') as f_img, open(config.people_file, 'w') as f_people, open(config.questions_file, 'w') as f_questions, open(config.answers_file, 'w') as f_answers:
            json.dump(data_images, f_img)
            json.dump(data_people, f_people)
            json.dump(data_questions, f_questions)
            json.dump(data_answers, f_answers)
        with open(config.images_file[:-2], 'w') as f_img, open(config.people_file[:-2], 'w') as f_people, open(config.questions_file[:-2], 'w') as f_questions, open(config.answers_file[:-2], 'w') as f_answers:
            f_img.write('var imagesUSGS = JSON.parse(\'')
            json.dump(data_images, f_img)
            f_img.write('\');')
            f_people.write('var peopleUSGS = JSON.parse(\'')
            json.dump(data_people, f_people)
            f_people.write('\');')
            f_questions.write('var questionsUSGS = JSON.parse(\'')
            json.dump(data_questions, f_questions)
            f_questions.write('\');')
            f_answers.write('var answersUSGS = JSON.parse(\'')
            json.dump(data_answers, f_answers)
            f_answers.write('\');')
    except:
        raise DatabaseException("Error: unable to write db.")

def add_image(original_name, sensor, upperleft_map_x, upperleft_map_y, res_x, res_y, people_id, type_img, image_data = None):
    image = {}
    image_id = len(data_images["images"])
    image["id"] = image_id
    image["date_added"] = time.time()
    image["original_name"] = os.path.basename(original_name)
    image["sensor"] = sensor
    image["upperleft_map_x"] = upperleft_map_x
    image["upperleft_map_y"] = upperleft_map_y
    image["res_x"] = res_x
    image["res_y"] = res_y
    image["people_id"] = people_id
    image["type"] = type_img
    image["questions_ids"] = []
    image["active"] = True
    data_images["images"].append(image)

	#save file
    if image_data is None:
        _, file_extension = os.path.splitext(original_name)
    try:
        if image_data is not None:
            PIL_img = Image.fromarray(image_data)
            PIL_img.save(config.image_folder + str(image_id) + '.png')
        else:
            print("Copy" + original_name)
            PIL_img = Image.open(original_name)
            PIL_img.save(config.image_folder + str(image_id) + '.png')
            os.rename(original_name, config.image_folder + str(image_id) + file_extension)
    except:
        raise DatabaseException("Error: unable to copy image.")

#update people
    try:
        data_people["people"][people_id]["images"].append(image_id)
    except:
        raise DatabaseException("Error: people_id " + str(people_id) + " is not defined.")
            
    return image_id


def add_question(img_id, people_id, type_question, question_str):
    question = {}
    question_id = len(data_questions["questions"])
    question["id"] = question_id
    question["date_added"] = time.time()
    question["img_id"] = img_id
    question["people_id"] = people_id
    question["type"] = type_question
    question["question"] = question_str
    question["answers_ids"] = []
    question["active"] = True
    data_questions["questions"].append(question)

    #updating image
    try:
        data_images["images"][img_id]["questions_ids"].append(question_id)
    except:
        raise DatabaseException("Error: image_id " + str(img_id) + " is not defined.")
	    
    #update people
    try:
        data_people["people"][people_id]["questions"].append(question_id)
    except:
        raise DatabaseException("Error: people_id " + str(people_id) + " is not defined.")
            
    return question_id


def add_answer(question_id, people_id, answer_str):
    answer = {}
    answer_id = len(data_answers["answers"])
    answer["id"] = answer_id
    answer["date_added"] = time.time()
    answer["question_id"] = question_id
    answer["people_id"] = people_id
    answer["answer"] = answer_str
    answer["active"] = True
    data_answers["answers"].append(answer)

	
    #updating question
    try:
        data_questions["questions"][question_id]["answers_ids"].append(answer_id)
    except:
        raise DatabaseException("Error: question_id " + str(question_id) + " is not defined.")

    #update people
    try:
        data_people["people"][people_id]["answers"].append(answer_id)
    except:
        raise DatabaseException("Error: people_id " + str(people_id) + " is not defined.")

    return answer_id


def add_people(login, password_hash, name, email):
    people = {}
    people["id"] = len(data_people["people"])
    people["date_added"] = time.time()
    people["login"] = login
    people["name"] = name
    people["email"] = email
    people["password_hash"] = password_hash
    people["images"] = []
    people["questions"] = []
    people["answers"] = []
    people["active"] = True
    data_people["people"].append(people)
    

#Database access:
#return set of ids matching key == value
def get_id_from_key(dbname, key, value):
    try:
        with open(db_files[dbname]) as f:
            data = json.load(f)
            answer = []
            for item in data[dbname]:
                if item[key] == value:
                    answer.append(item["id"])
            return answer
    except:
        raise DatabaseException("Error: unable to open " + db_files[dbname] + ".")
        
def get_id_from_startkey(dbname, key, value):
    try:
        with open(db_files[dbname]) as f:
            data = json.load(f)
            answer = []
            for item in data[dbname]:
                if item[key].startswith(value):
                    answer.append(item["id"])
            return answer
    except:
        raise DatabaseException("Error: unable to open " + db_files[dbname] + ".")

def get_db(dbname):
    try:
        with open(db_files[dbname]) as f:
            data = json.load(f)
    except:
        raise DatabaseException("Error: unable to open " + db_files[dbname] + ".")

    return data[dbname]

