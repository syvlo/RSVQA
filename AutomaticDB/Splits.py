#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 16:59:59 2019

@author: sylvain
"""

# Définition des découpages des bases de données en entraînement/validation/test

import os
import re
import rasterio
import DatabaseIO as db
import json

create_csv = False
output_csv_name = "USGS_split_{}.csv"
create_sub_db = False
output_subdb_name = "USGS_split_{}_{}"
folder = './USGS_OriginalTiles'
test_tiles = ['992235', '992232', '992230', '992227', '992225', '992222', '992220', '992217', '992215', '992212',\
              '982217', '982215', '982212', '982210', '982207', '982205', '982202', '982200', '982197', '982195',\
              '057207', 'l_10650222_06_04800_col_2007', '052220', '025215', 'l_13410288_06_07400_4bd_2013',\
              'l_13590274_06_07400_4bd_2013', '997242', '000242', '995240', '997240', '000240', '022202',\
              '060202']
test_tiles_phili = ['692237', '695235', '692227', '692235', '687222', '690225', '697235', '687225',\
                    '687237', '690235', '690227']#Out of 39 tiles originally
val_tiles = ['985222', '985220', '985217', '985215', '985212', '985210', '985207', '985205', '985202', '985200',\
             'l_11400210_06_05500_4bd_2010', 'l_13890306_06_07400_4bd_2013',\
             'l_13860314_06_05500_4bd_2010', 'l_14070320_06_07400_4bd_2013', 'l_11580192_06_04800_col_2007',\
             'l_14370352_06_05500_4bd_2010', 'l_14430346_06_07400_4bd_2013', '990222']
to_exclude = ['l_11340226_06_04800_col_2007', '217622', '242620', '260640', '235585', '29834280', '29263680', '28962700']
train_tiles = [os.path.splitext(os.path.basename(file))[0] for file in os.listdir(folder)\
               if os.path.splitext(os.path.basename(file))[0] not in test_tiles and\
               os.path.splitext(os.path.basename(file))[0] not in test_tiles_phili and\
               os.path.splitext(os.path.basename(file))[0] not in val_tiles and\
               os.path.splitext(os.path.basename(file))[0] not in to_exclude]

number_tiles = len(train_tiles) + len(val_tiles) + len(test_tiles) + len(test_tiles_phili)
print("Splits (original tiles level):")
print("- train: %i (%0.2f%%)" % (len(train_tiles), len(train_tiles) / number_tiles*100))
print("- val: %i (%0.2f%%)" % (len(val_tiles), len(val_tiles) / number_tiles*100))
print("- test: %i (%0.2f%%)" % (len(test_tiles), len(test_tiles) / number_tiles* 100.0))
print("- test philadelphia: %i (%0.2f%%)" % (len(test_tiles_phili), len(test_tiles_phili) / number_tiles* 100.0))

if create_csv:
    splits = [test_tiles, test_tiles_phili, val_tiles, train_tiles]
    for i, split in enumerate(["test", "test_philadelphia", "val", "train"]):
        with open(output_csv_name.format(split), 'w') as csv:
            csv.write("X, Y\n")
            for image_index in splits[i]:
                image_name = os.path.join(folder, image_index+'.tif')
                with rasterio.open(image_name) as image:
                    top_left_X, bottom_right_Y,bottom_right_X, top_right_Y = image.bounds
                    X = bottom_right_X - (bottom_right_X - top_left_X)/2
                    Y = top_right_Y - (top_right_Y - bottom_right_Y)/2
                    csv.write(str(X) + ", " + str(Y) + "\n")


if create_sub_db:
    db_images = db.get_db("images")
    images_test = []
    images_test_phili = []
    images_val = []
    images_train = []
    p = re.compile("(\w+)_\d+-\d+")
    for image_index in range(len(db_images)):
        entry = db_images[image_index]
        empty_entry = {'id': image_index, 'active': False}
        original_name = os.path.splitext(entry['original_name'])[0]
        image_name = p.match(original_name).group(1)
        if image_name in test_tiles:
            images_test.append(entry)
            images_val.append(empty_entry)
            images_train.append(empty_entry)
            images_test_phili.append(empty_entry)
        else:
            if image_name in val_tiles:
                images_val.append(entry)
                images_train.append(empty_entry)
                images_test_phili.append(empty_entry)
                images_test.append(empty_entry)
            else:
                if image_name in train_tiles:
                    images_train.append(entry)
                    images_test_phili.append(empty_entry)
                    images_test.append(empty_entry)
                    images_val.append(empty_entry)
                else:
                    if image_name in test_tiles_phili:
                        images_test_phili.append(entry)
                        images_train.append(empty_entry)
                        images_test.append(empty_entry)
                        images_val.append(empty_entry)
                    else:
                        images_test_phili.append(empty_entry)
                        images_train.append(empty_entry)
                        images_test.append(empty_entry)
                        images_val.append(empty_entry)
                        if image_name not in to_exclude:
                            print("Something went wrong, could not find " + image_name + " in the splits.")
                            break
                
    number_images = len(images_train) + len(images_val) + len(images_test) + len(images_test_phili)
    print("Splits (images level):")
    print("- train: %i (%0.2f%%)" % (len(images_train), len(images_train) / number_images*100))
    print("- val: %i (%0.2f%%)" % (len(images_val), len(images_val) / number_images*100))
    print("- test: %i (%0.2f%%)" % (len(images_test), len(images_test) / number_images* 100.0))
    print("- test philadelphia: %i (%0.2f%%)" % (len(images_test_phili), len(images_test_phili) / number_images* 100.0))
    
    
    def get_questions(subset_images, questions):
        questions_out = []
        last_question_id = 0
        for image_index in range(len(subset_images)):
            if subset_images[image_index]["active"]:
                questions_ids = subset_images[image_index]["questions_ids"]
                while last_question_id < questions_ids[0]:
                    questions_out.append({'id':last_question_id, 'active': False})
                    last_question_id += 1
                for question_id in questions_ids:
                    questions_out.append(questions[question_id])
                last_question_id = question_id + 1
        return questions_out
        
    db_questions = db.get_db("questions")
    questions_test = get_questions(images_test, db_questions)
    questions_test_phili = get_questions(images_test_phili, db_questions)
    questions_val = get_questions(images_val, db_questions)
    questions_train = get_questions(images_train, db_questions)
    
    def get_answers(subset_questions, answers):
        answers_out = []
        last_answer_id = 0
        for question_index in range(len(subset_questions)):
            if subset_questions[question_index]["active"]:
                answers_ids = subset_questions[question_index]["answers_ids"]
                while last_answer_id < answers_ids[0]:
                    answers_out.append({'id':last_answer_id, 'active': False})
                    last_answer_id += 1
                for answers_id in answers_ids:
                    answers_out.append(answers[answers_id])
                last_answer_id = answers_id + 1
        return answers_out
    
    db_answers = db.get_db("answers")
    answers_test = get_answers(questions_test, db_answers)
    answers_test_phili = get_answers(questions_test_phili, db_answers)
    answers_val = get_answers(questions_val, db_answers)
    answers_train = get_answers(questions_train, db_answers)
    
    for split in ["train", "test", "val", "test_phili"]:
        if split == "train":
            data_images = {"images": images_train}
            data_questions = {"questions": questions_train}
            data_answers = {"answers": answers_train}
        if split == "val":
            data_images = {"images": images_val}
            data_questions = {"questions": questions_val}
            data_answers = {"answers": answers_val}
        if split == "test":
            data_images = {"images": images_test}
            data_questions = {"questions": questions_test}
            data_answers = {"answers": answers_test}
        if split == "test_phili":
            data_images = {"images": images_test_phili}
            data_questions = {"questions": questions_test_phili}
            data_answers = {"answers": answers_test_phili}
            
        with open(output_subdb_name.format(split, "images")+".json", 'w') as f_img, open(output_subdb_name.format(split, "questions")+".json", 'w') as f_questions, open(output_subdb_name.format(split, "answers")+".json", 'w') as f_answers:
            json.dump(data_images, f_img)
            json.dump(data_questions, f_questions)
            json.dump(data_answers, f_answers)
        with open(output_subdb_name.format(split, "images")+".js", 'w') as f_img, open(output_subdb_name.format(split, "questions")+".js", 'w') as f_questions, open(output_subdb_name.format(split, "answers")+".js", 'w') as f_answers:
            f_img.write('var imagesUSGS = JSON.parse(\'')
            json.dump(data_images, f_img)
            f_img.write('\');')
            f_questions.write('var questionsUSGS = JSON.parse(\'')
            json.dump(data_questions, f_questions)
            f_questions.write('\');')
            f_answers.write('var answersUSGS = JSON.parse(\'')
            json.dump(data_answers, f_answers)
            f_answers.write('\');')
