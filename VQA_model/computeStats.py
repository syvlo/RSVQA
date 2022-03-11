#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: sylvain
"""

# Calcul des statistiques sur un jeu de test

import VocabEncoder
import VQALoader
from models import model
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import torch
import torchvision.transforms as T
from torch.autograd import Variable
from skimage import io
import numpy as np
import pickle
import os

def do_confusion_matrix(all_mat, old_vocab, new_vocab, dataset):
    print(new_vocab)
    new_mat = np.zeros((len(new_vocab), len(new_vocab)))
    for i in range(1,all_mat.shape[0]):
        answer = old_vocab[i]
        new_i = new_vocab.index(answer)
        for j in range(1,all_mat.shape[1]):
            answer = old_vocab[j]
            new_j = new_vocab.index(answer)
            new_mat[new_i, new_j] = all_mat[i, j]

    if len(old_vocab) > 20:#HR
        new_mat = new_mat[0:18,0:18]
        new_vocab = new_vocab[0:18]
    fig = plt.figure(figsize=(10,5))
    ax = fig.add_subplot(111)
    cax = ax.matshow(np.log(new_mat+1), cmap="YlGn")
    #plt.title('Confusion matrix of the classifier')
    fig.colorbar(cax)
    ax.set_xticklabels([''] + new_vocab)
    ax.set_yticklabels([''] + new_vocab)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.show()
    fig.savefig('confusion_matrix_' + dataset + '.svg')
    #plt.close()

        

def get_vocab(dataset):
    data_path = '../AutomaticDB/'
    if dataset == "LR":
        allanswersJSON = os.path.join(data_path, 'answers.json')
        encoder_answers = VocabEncoder.VocabEncoder(allanswersJSON, questions=False, range_numbers = True)
    else:
        allanswersJSON = os.path.join(data_path, 'USGSanswers.json')
        encoder_answers = VocabEncoder.VocabEncoder(allanswersJSON, questions=False, range_numbers = False)
        
    return encoder_answers.getVocab()

def run(experiment, dataset, shuffle=False, num_batches=-1, save_output=False):
    print ('---' + experiment + '---')
    batch_size = 100
    data_path = '../AutomaticDB/'
    if dataset == "LR":
        allquestionsJSON = os.path.join(data_path, 'questions.json')
        allanswersJSON = os.path.join(data_path, 'answers.json')
        questionsJSON = os.path.join(data_path, 'LR_split_test_questions.json')
        answersJSON = os.path.join(data_path, 'LR_split_test_answers.json')
        imagesJSON = os.path.join(data_path, 'LR_split_test_images.json')
        images_path = os.path.join(data_path, 'data/')
        encoder_questions = VocabEncoder.VocabEncoder(allquestionsJSON, questions=True)
        encoder_answers = VocabEncoder.VocabEncoder(allanswersJSON, questions=False, range_numbers = True)
        patch_size = 256
    else:
        allquestionsJSON = os.path.join(data_path, 'USGSquestions.json')
        allanswersJSON = os.path.join(data_path, 'USGSanswers.json')
        if dataset == "HR":
            questionsJSON = os.path.join(data_path, 'USGS_split_test_questions.json')
            answersJSON = os.path.join(data_path, 'USGS_split_test_answers.json')
            imagesJSON = os.path.join(data_path, 'USGS_split_test_images.json')
        else:
            questionsJSON = os.path.join(data_path, 'USGS_split_test_phili_questions.json')
            answersJSON = os.path.join(data_path, 'USGS_split_test_phili_answers.json')
            imagesJSON = os.path.join(data_path, 'USGS_split_test_phili_images.json')
        images_path = os.path.join(data_path, 'dataUSGS/')
        encoder_questions = VocabEncoder.VocabEncoder(allquestionsJSON, questions=True)
        encoder_answers = VocabEncoder.VocabEncoder(allanswersJSON, questions=False, range_numbers = False)
        patch_size = 512

    weight_file = 'Model' + experiment + '.pth'
    network = model.VQAModel(encoder_questions.getVocab(), encoder_answers.getVocab(), input_size = patch_size).cuda()
    state = network.state_dict()
    state.update(torch.load(weight_file))
    network.load_state_dict(state)
    network.eval().cuda()
    
    IMAGENET_MEAN = [0.485, 0.456, 0.406]
    IMAGENET_STD = [0.229, 0.224, 0.225]
    transform = T.Compose([
        T.ToTensor(),            
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
      ])
    test_dataset = VQALoader.VQALoader(images_path, imagesJSON, questionsJSON, answersJSON, encoder_questions, encoder_answers, train=False, ratio_images_to_use=1, transform=transform, patch_size = patch_size)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=True, num_workers=2)

    if dataset == 'LR':
        countQuestionType = {'rural_urban': 0, 'presence': 0, 'count': 0, 'comp': 0}
        rightAnswerByQuestionType = {'rural_urban': 0, 'presence': 0, 'count': 0, 'comp': 0}
    else:
        countQuestionType = {'area': 0, 'presence': 0, 'count': 0, 'comp': 0}
        rightAnswerByQuestionType = {'area': 0, 'presence': 0, 'count': 0, 'comp': 0}
    confusionMatrix = np.zeros((len(encoder_answers.getVocab()), len(encoder_answers.getVocab())))
    
    for i, data in enumerate(test_loader, 0):
        if num_batches == 0:
            break
        num_batches -= 1
        if i % 100 == 99:
            print(float(i) / len(test_loader))
        question, answer, image, type_str, image_original = data
        question = Variable(question.long()).cuda()
        answer = Variable(answer.long()).cuda().resize_(question.shape[0])
        if shuffle:
            order = np.array(range(image.shape[0]))
            np.random.shuffle(order)
            image[np.array(range(image.shape[0]))] = image[order]
        image = Variable(image.float()).cuda()
        pred = network(image,question)
        
        answer = answer.cpu().numpy()
        pred = np.argmax(pred.cpu().detach().numpy(), axis=1)
        
        for j in range(answer.shape[0]):
            countQuestionType[type_str[j]] += 1
            if answer[j] == pred[j]:
                rightAnswerByQuestionType[type_str[j]] += 1
            confusionMatrix[answer[j], pred[j]] += 1
            
        if save_output:
            out_path = 'output_' + experiment + '_' + dataset
            if not os.path.exists(out_path):
                os.mkdir(out_path)
            for j in range(batch_size):
                viz_img = T.ToPILImage()(image_original[j].float().data.cpu())
                viz_question = encoder_questions.decode(question[j].data.cpu().numpy())
                viz_answer = encoder_answers.decode([answer[j]])
                viz_pred = encoder_answers.decode([pred[j]])
            
                imname = str(i * batch_size + j) + '_q_' + viz_question + '_gt_' + viz_answer + '_pred_' + viz_pred + '.png'
                plt.imsave(os.path.join(out_path, imname), viz_img)
    
    Accuracies = {'AA': 0}
    for type_str in countQuestionType.keys():
        Accuracies[type_str] = rightAnswerByQuestionType[type_str] * 1.0 / countQuestionType[type_str]
        Accuracies['AA'] += Accuracies[type_str] / len(countQuestionType.keys())
    Accuracies['OA'] = np.trace(confusionMatrix)/np.sum(confusionMatrix)
    
    print('- Accuracies')
    for type_str in countQuestionType.keys():
        print (' - ' + type_str + ': ' + str(Accuracies[type_str]))
    print('- AA: ' + str(Accuracies['AA']))
    print('- OA: ' + str(Accuracies['OA']))
    
    return Accuracies, confusionMatrix


#expes = {'LRs': ['427f37d306ef4d03bb1406d5cd20336f', 'bd1387960b624257b9a50924d8134be6', '899e11235c624ec9bbb66e26da52d6fc'],
#         'LR': ['427f37d306ef4d03bb1406d5cd20336f', 'bd1387960b624257b9a50924d8134be6', '899e11235c624ec9bbb66e26da52d6fc'],
#         'HR': ['65f94a4f7ccd491da362f73e46795d26', '988853ae5d5e441695f98ee506021bdf', '3bfd251cafb74d379d02bf59d383381a'],
#         'HRPhili': ['65f94a4f7ccd491da362f73e46795d26', '988853ae5d5e441695f98ee506021bdf', '3bfd251cafb74d379d02bf59d383381a'],
#         'HRs': ['65f94a4f7ccd491da362f73e46795d26', '988853ae5d5e441695f98ee506021bdf', '3bfd251cafb74d379d02bf59d383381a'],
#         'HRPhilis': ['65f94a4f7ccd491da362f73e46795d26', '988853ae5d5e441695f98ee506021bdf', '3bfd251cafb74d379d02bf59d383381a']}
expes = {'LR': ['427f37d306ef4d03bb1406d5cd20336f', 'bd1387960b624257b9a50924d8134be6', '899e11235c624ec9bbb66e26da52d6fc'],
         'HR': ['65f94a4f7ccd491da362f73e46795d26', '988853ae5d5e441695f98ee506021bdf', '3bfd251cafb74d379d02bf59d383381a'],
         'HRPhili': ['65f94a4f7ccd491da362f73e46795d26', '988853ae5d5e441695f98ee506021bdf', '3bfd251cafb74d379d02bf59d383381a']}
run('65f94a4f7ccd491da362f73e46795d26', 'HR', num_batches=5, save_output=True)
run('65f94a4f7ccd491da362f73e46795d26', 'HRPhili', num_batches=5, save_output=True)
run('427f37d306ef4d03bb1406d5cd20336f', 'LR', num_batches=5, save_output=True)
for dataset in expes.keys():
    acc = []
    mat = []
    for experiment_name in expes[dataset]:
        if not os.path.isfile('accuracies_' + dataset + '_' + experiment_name + '.npy'):
            if dataset[-1] == 's':
                tmp_acc, tmp_mat = run(experiment_name, dataset[:-1], shuffle=True)
            else:
                tmp_acc, tmp_mat = run(experiment_name, dataset)
            np.save('accuracies_' + dataset + '_' + experiment_name, tmp_acc)
            np.save('confusion_matrix_' + dataset + '_' + experiment_name, tmp_mat)
        else:
            tmp_acc = np.load('accuracies_' + dataset + '_' + experiment_name + '.npy')[()]
            tmp_mat = np.load('confusion_matrix_' + dataset + '_' + experiment_name + '.npy')[()]
        acc.append(tmp_acc)
        mat.append(tmp_mat)
        
    print('--- Total (' + dataset + ') ---')
    print('- Accuracies')
    for type_str in tmp_acc.keys():
        all_acc = []
        for tmp_acc in acc:
            all_acc.append(tmp_acc[type_str])
        print(' - ' + type_str + ': ' + str(np.mean(all_acc)) + ' ( stddev = ' + str(np.std(all_acc)) + ')')
    
    if dataset[-1] == 's':
        vocab = get_vocab(dataset[:-1])
    else:
        vocab = get_vocab(dataset)

    all_mat = np.zeros(tmp_mat.shape)    
    for tmp_mat in mat:
        all_mat += tmp_mat
    
    if dataset[0] == 'H':
        new_vocab = ['yes', 'no', '0m2', 'between 0m2 and 10m2', 'between 10m2 and 100m2', 'between 100m2 and 1000m2', 'more than 1000m2'] + [str(i) for i in range(90)]
    else:
        new_vocab = ['yes', 'no', 'rural', 'urban', '0', 'between 0 and 10', 'between 10 and 100', 'between 100 and 1000', 'more than 1000']
        
    do_confusion_matrix(all_mat, vocab, new_vocab, dataset)


#labels = ['Yes', 'No', '<=10', '0', '<=100', '<=1000', '>1000', 'Rural', 'Urban']
#fig = plt.figure()
#ax = fig.add_subplot(111)
#cax = ax.matshow(np.log(confusionMatrix[1:,1:] + 1), cmap="YlGn")
##plt.title('Confusion matrix of the classifier')
#fig.colorbar(cax)
#ax.set_xticklabels([''] + labels)
#ax.set_yticklabels([''] + labels)
#plt.xlabel('Predicted')
#plt.ylabel('True')
#plt.show()
#fig.savefig(os.path.join(baseFolder, 'AccMatrix.pdf'))
#print(Accuracies)
