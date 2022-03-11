#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: sylvain
"""
# Moteur de construction de questions.

import random
import numpy as np
import DatabaseIO as db
import time

class ConstructImageQuestion():
    def __init__(self, featureDict):
        self.features = featureDict
        self.questions = []
        self.answers = []
        self.canonical_questions = []

        # Le type est défini ainsi [proba, function, args] (voir exemples ci-dessous)
        self.QUESTION_TYPES = {}
        # Activer ou desactiver selon le type de question choisi
        # self.QUESTION_TYPES['rural_urban'] = [0, self.ruralUrban, 0]
        self.QUESTION_TYPES['presence'] = [0.5, self.presence, 1]
        self.QUESTION_TYPES['count'] = [0.5, self.count, 1]
        self.QUESTION_TYPES['less_more_equal'] = [0.1, self.less_more_equal, 2]
        self.QUESTION_TYPES['area'] = [0.2, self.area, 1]
        #self.QUESTION_TYPES['population'] = [0.1, self.population, 0]


    def writeInDB(self, imageName, upperleft_x, upperleft_y):
        USER_ID = 0
        
        img_id = db.add_image(imageName, 'ULTRACAM_EAGLE_FALCON', upperleft_x, upperleft_y, ".1524m", ".1524m", 0, "RGB")
        print(self.questions)
        for i in range(len(self.questions)):
            question_id = db.add_question(img_id, USER_ID, self.canonical_questions[i][0], self.questions[i])
            db.add_answer(question_id, USER_ID, self.answers[i])
    
    def chooseQuestionsToAsk(self, numberQuestion):
        startWhole = time.time()
#        question, answer = self.ruralUrban()
#        self.questions.append(question)
#        self.answers.append(answer)
#        
#        self.canonical_questions.append(['rural_urban'])
        tries = 0
        while len(self.questions) < numberQuestion and tries < 10000:
            for question in self.QUESTION_TYPES:
                tries += 1
                if random.random() < self.QUESTION_TYPES[question][0]:
                    start = time.time()
                    question, answer, canonical_question = self.QUESTION_TYPES[question][1]()
                    if random.random() < .1:
                        question += ' in the image'
                    question += '?'
                    end = time.time()
                    #print('Q: ' + question + ', time = ' + str(end - start))
                    
                    if question != ' in the image?' and question != '?' and canonical_question not in self.canonical_questions:
                        self.questions.append(question)
                        self.answers.append(answer)
                        self.canonical_questions.append(canonical_question)
        print(tries)
        endWhole = time.time()
        print('Time elapsed = ' + str(endWhole - startWhole))
                        
    
    def ruralUrban(self):
        #print('ruralUrban')
        question = 'Is it a rural or an urban area'
        answer = 'rural'
        if 'import.osm_buildings' in self.features and len(self.features['import.osm_buildings']) > 2:
            answer = 'urban'
        return question, answer
            
    def presence(self):
        #print('presence')
        objects = Objects(self.features, plural=False)
        if not objects.success:
            return '', '', ''
        answer = 'no'
        if objects.count > 0:
            answer = 'yes'
        choices = ['Is there a' + objects.string,\
                   'Is a' + objects.string + ' present']
        question = choices[random.randint(0,len(choices) - 1)]
        return question, answer, ['presence', objects.string]
    
    def count(self):
        #print('count')
        objects = Objects(self.features, plural=True)
        if not objects.success:
            return '', '', ''
        answer = str(objects.count)
        choices = ['How many' + objects.string + ' are there',\
                   'What is the number of' + objects.string,\
                   'What is the amount of' + objects.string]
        question = choices[random.randint(0,len(choices) - 1)]
        return question, answer, ['count', objects.string]
    
    def less_more_equal(self):
        #print('less more')
        obj1 = Objects(self.features, plural=True)
        obj2 = Objects(self.features, plural=True, exclude=obj1.type)
        
        if not obj1.success or not obj2.success:
            return '', '', ''
        
        choice = random.randint(0,2)
        answer = 'no'
        if choice == 0:#less
            question = 'Are there less' + obj1.string + ' than' + obj2.string
            if obj1.count < obj2.count:
                answer = 'yes'
        if choice == 1:#more
            question = 'Are there more' + obj1.string + ' than' + obj2.string
            if obj1.count > obj2.count:
                answer = 'yes'
        if choice == 2:#equal
            question = 'Is the number of' + obj1.string + ' equal to the number of' + obj2.string
            if obj1.count == obj2.count:
                answer = 'yes'
        return question, answer, ['comp', choice, obj1.string, obj2.string]
    
    def area(self):
        obj1 = Objects(self.features, plural=True, exclude='import.osm_roads')
        
        if not obj1.success:
            return '', '', ''
        
        area = 0
        for obj in obj1.object_list:
            area += obj.area
            
        question = 'What is the area covered by' + obj1.string
        answer = str(int(area)) + 'm2'
        return question, answer, ['area', obj1.string]
    
    def population(self):
        obj1 = Objects(self.features, plural=True, choose='residential building')

        if not obj1.success:
            return '', '', ''
        
        area = 0
        for obj in obj1.object_list:
            area += obj.area
        population = int(area / 15)
        
        question = 'How many people live in this area'
        answer = str(population)
        return question, answer, ['population']


class Objects():
    def __init__(self, features, plural, relation=True, exclude=None, choose=None):
        self.features = features
        self.exclude = exclude
        self.choose = choose
        self.count = 0
        self.plural = plural
        self.string = 'ERROR'
        self.type = 'None'
        self.object_list = []
        self.PROBA_ATTRIBUTE = .1
        self.ATTRIBUTES = {}
        self.ATTRIBUTES['size'] = ['small', 'medium', 'large']
        self.ATTRIBUTES['shape'] = ['square', 'rectangular', 'circular']
        self.LAND_USES = ['residential area', 'grass area', 'commercial area', 'construction area', 'industrial area', 'allotment', 'cemetery', 'depot', 'farmland', 'farmyard', 'forest', 'garage', 'greenfield', 'landfill', 'meadow', 'military area', 'orchard', 'port', 'railway', 'recreation ground', 'religious area', 'salt pond', 'vineyard']

        self.relation_proba = .02
        self.RELATIONS = ['at the top of', 'on the right of', 'at the bottom of', 'on the left of', 'next to']
        self.DISTANCE_CLOSE = 1000
        
        self.BASEOBJECTS = []
        #type: [name, OSMName]
        self.BASEOBJECTS.append(['building', 'import.osm_buildings'])
        self.BASEOBJECTS.append(['residential building', 'import.osm_buildings'])
        self.BASEOBJECTS.append(['commercial building', 'import.osm_buildings'])
        self.BASEOBJECTS.append(['road', 'import.osm_roads'])
        self.BASEOBJECTS.append(['water area', 'import.osm_waterareas'])
        self.BASEOBJECTS.append(['land class', 'import.osm_landusages'])
        self.success = False
        if random.random() < self.relation_proba and relation:
            self.success = self.relation(random.randrange(0,5))
        if not self.success:
            self.success = self.constructObjects()
            
    def relation(self, relation_type):
        obj1 = Objects(self.features, self.plural, relation=False)
        obj2 = Objects(self.features, plural=False, relation=False, exclude=obj1.type)
        if not obj2.success:
            return False
        self.string = obj1.string + ' '+  self.RELATIONS[relation_type]
        if obj2.count == 1:
            self.string += ' the '
        else:
            self.string += ' a '
        self.string += obj2.string
        
        start = time.time()
        for obj_2 in obj2.object_list:
            obj2_coord = [(obj_2.bounds[0] + obj_2.bounds[2]) / 2, (obj_2.bounds[1] +obj_2.bounds[3]) / 2]
            for obj in obj1.object_list:
                if obj in self.object_list:
                    continue
                if relation_type == 0 and obj.bounds[1] > obj2_coord[1]\
                or relation_type == 1 and obj.bounds[0] > obj2_coord[0]\
                or relation_type == 2 and obj.bounds[3] < obj2_coord[1]\
                or relation_type == 3 and obj.bounds[2] < obj2_coord[0]\
                or relation_type == 4 and obj.distance(obj_2) < self.DISTANCE_CLOSE:
                    self.object_list.append(obj)
                    self.count += 1
                if time.time() - start > 5:
                    return False
                    
                
        return True
        
    def check_attr(self, attribute_type, attribute_number, obj):
        if attribute_type == None:
            return True
        if attribute_type == 'size':
            area = obj.area
            if attribute_number == 0 and area < 100\
            or attribute_number == 1 and area >= 100 and area < 500\
            or attribute_number == 2 and area >= 500:
                return True
        if attribute_type == 'shape' and obj.geom_type == 'Polygon':
            circle_area = obj.length**2/(4*np.pi)
            area_perim_ratio = obj.area/obj.length
            if attribute_number == 0 and area_perim_ratio > 0.9*obj.length and area_perim_ratio < 1.1 * obj.length\
            or attribute_number == 1 and len(obj.exterior.coords) < 8\
            or circle_area > 0.9 * obj.area and circle_area < 1.1 * obj.area:
                return True
        return False
            
            
        
    def constructObjects(self):
        choice_object = np.random.permutation(6)
        choice_attribute_type = np.random.permutation(2)
        choice_attribute = np.random.permutation(3)
        attr = None
        if random.random() < self.PROBA_ATTRIBUTE:
            if choice_attribute_type[0] == 0:
                attr = 'size'
            else:
                attr = 'shape'
        for choice in choice_object:
            if self.BASEOBJECTS[choice][0] == 'road':
                attr = None
            if self.choose:
                for i, elt in enumerate(self.BASEOBJECTS):
                    if elt[0] == self.choose:
                        choice = i
            if self.BASEOBJECTS[choice][1] == self.exclude:
                continue
            if self.BASEOBJECTS[choice][1] not in self.features:
                if random.random() > 0.1:
                    continue
                if self.BASEOBJECTS[choice][0] == 'land class':
                    type_land = self.LAND_USES[random.randint(0, len(self.LAND_USES) - 1)]
            else:
                if self.BASEOBJECTS[choice][0] == 'land class':
                    type_land = self.features[self.BASEOBJECTS[choice][1]][random.randint(0, len(self.features[self.BASEOBJECTS[choice][1]]) - 1)][1]
                for obj in self.features[self.BASEOBJECTS[choice][1]]:
                    if self.BASEOBJECTS[choice][0] == 'land class':
                        if obj[1] == type_land:
                            obj = obj[0]
                        else:
                            continue
                    if self.BASEOBJECTS[choice][0] == 'residential building':
                        if obj[1] == 'residential':
                            obj = obj[0]
                        else:
                            continue   
                    if self.BASEOBJECTS[choice][0] == 'commercial building':
                        if obj[1] == 'commercial':
                            obj = obj[0]
                        else:
                            continue
                    if self.BASEOBJECTS[choice][0] == 'building':
                        obj=obj[0]
                    if self.check_attr(attr, choice_attribute[0], obj):
                        self.object_list.append(obj)
            self.type = self.BASEOBJECTS[choice][1]
            
            self.string = ''
            if attr == 'size':
                self.string = ' ' + self.ATTRIBUTES['size'][choice_attribute[0]]
            if attr == 'shape':
                self.string = ' ' + self.ATTRIBUTES['shape'][choice_attribute[0]]
            if self.BASEOBJECTS[choice][0] == 'land class':
                self.string += ' ' + type_land
            else:
                self.string += ' ' + self.BASEOBJECTS[choice][0]
            if self.plural:
                self.string += 's'
            self.count = len(self.object_list)
            return True
        return False
            
            
                    
                
            
            
        
        
                
                
