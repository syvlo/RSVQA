#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: sylvain
"""

# Encodeur du vocabulaireß

import json

MAX_ANSWERS = 100
LEN_QUESTION = 20


class VocabEncoder():
    # Création du dictionnaire en parcourant l'ensemble du JSON (des questions ou des réponses)
    def __init__(self, JSONFile, string=None, questions=True, range_numbers=False):
        self.encoder_type = 'answer'
        if questions:
            self.encoder_type = 'question'
        self.questions = questions
        self.range_numbers = range_numbers
        
        words = {}  
        
        if JSONFile != None:
            with open(JSONFile) as json_data:
                self.data = json.load(json_data)[self.encoder_type + 's']
        else:
            if questions:
                self.data = [{'question':string}]
            else:
                self.data = [{'answer':string}]
            
        
        for i in range(len(self.data)):
            if self.data[i]["active"]:
                sentence = self.data[i][self.encoder_type]
                if sentence[-1] == "?" or sentence[-1] == ".":
                    sentence = sentence[:-1]
                
                tokens = sentence.split()
                for token in tokens:
                    token = token.lower()
                    if range_numbers and token.isdigit() and not questions:
                        num = int(token)
                        if num > 0 and num <= 10:
                            token = "between 0 and 10"
                        if num > 10 and num <= 100:
                            token = "between 10 and 100"
                        if num > 100 and num <= 1000:
                            token = "between 100 and 1000"
                        if num > 1000:
                            token = "more than 1000"

                    if token[-2:] == 'm2' and not questions:
                        num = int(token[:-2])
                        if num > 0 and num <= 10:
                            token = "between 0m2 and 10m2"
                        if num > 10 and num <= 100:
                            token = "between 10m2 and 100m2"
                        if num > 100 and num <= 1000:
                            token = "between 100m2 and 1000m2"
                        if num > 1000:
                            token = "more than 1000m2"
                    if token not in words:
                        words[token] = 1
                    else:
                        words[token] += 1
                
        sorted_words = sorted(words.items(), key=lambda kv: kv[1], reverse=True)
        self.words = {'<EOS>':0}
        self.list_words = ['<EOS>']
        for i, word in enumerate(sorted_words):
            if self.encoder_type == 'answer':
                if i >= MAX_ANSWERS:
                    break
            self.words[word[0]] = i + 1
            self.list_words.append(word[0])
    
    #Encodage d'une phrase (question ou réponse) à partir du dictionnaire crée plus tôt.        
    def encode(self, sentence):
        res = []
        if sentence[-1] == "?" or sentence[-1] == ".":
            sentence = sentence[:-1]
            
        tokens = sentence.split()
        for token in tokens:
            token = token.lower()
            if self.range_numbers and token.isdigit() and not self.questions:
                num = int(token)
                if num > 0 and num <= 10:
                    token = "between 0 and 10"
                if num > 10 and num <= 100:
                    token = "between 10 and 100"
                if num > 100 and num <= 1000:
                    token = "between 100 and 1000"
                if num > 1000:
                    token = "more than 1000"
                    
            if token[-2:] == 'm2' and not self.questions:
                num = int(token[:-2])
                if num > 0 and num <= 10:
                    token = "between 0m2 and 10m2"
                if num > 10 and num <= 100:
                    token = "between 10m2 and 100m2"
                if num > 100 and num <= 1000:
                    token = "between 100m2 and 1000m2"
                if num > 1000:
                    token = "more than 1000m2"
            res.append(self.words[token])
        
        if self.questions:
            res.append(self.words['<EOS>'])
        
        if self.questions:
            while len(res) < LEN_QUESTION:
                res.append(self.words['<EOS>'])
            res = res[:LEN_QUESTION]
        return res
    
    
    def getVocab(self):
        return self.list_words
    
    #Décodage d'une phrase (seulement utilisé pour l'affichage des résultats)
    def decode(self, sentence):
        res = ""
        for i in sentence:
            if i == 0:
                break
            res += self.list_words[i]
            res += " "
        res = res[:-1]
        if self.questions:
            res += "?"
        return res
        
            
            
            
        