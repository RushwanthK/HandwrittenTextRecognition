import sys
import argparse
import cv2
import editdistance
from DataLoader import DataLoader, Batch
from Model import Model, DecoderType
from SamplePreprocessor import preprocess
import streamlit as st
import os

class FilePaths:
  image_file = st.file_uploader("Upload An Image to predict the word",type=['png','jpeg','jpg'])
  if image_file is not None:
    file_details = {"FileName":image_file.name,"FileType":image_file.type}
    with open(os.path.join("/content/drive/MyDrive/SimpleHTR/data",image_file.name),"wb") as f:
      f.write(image_file.getbuffer())
    path = os.path.join("/content/drive/MyDrive/SimpleHTR/data",image_file.name)
    st.success("Saved File")
  fnCharList = '../model/charList.txt'
  fnAccuracy = '../model/accuracy.txt'
  fnTrain = '../data/'
    #fnInfer = 'path'
  fnCorpus = '../data/corpus.txt'


def train(model, loader):
  epoch = 0 # number of training epochs since start
  bestCharErrorRate = float('inf') # best valdiation character error rate
  noImprovementSince = 0 # number of epochs no improvement of character error rate occured
  earlyStopping = 5 # stop training after this number of epochs without improvement
  while True:
    epoch += 1
    loader.trainSet()
    while loader.hasNext():
      iterInfo = loader.getIteratorInfo()
      batch = loader.getNext()
      loss = model.trainBatch(batch)
    charErrorRate = validate(model, loader)
        
        # if best validation accuracy so far, save model parameters
    if charErrorRate < bestCharErrorRate:
            #print('Character error rate improved, save model')
      bestCharErrorRate = charErrorRate
      noImprovementSince = 0
      model.save()
      open(FilePaths.fnAccuracy, 'w').write('Validation character error rate of saved model: %f%%' % (charErrorRate*100.0))
    else:
            #print('Character error rate not improved')
      noImprovementSince += 1

        # stop training if no more improvement in the last x epochs
    if noImprovementSince >= earlyStopping:
            #print('No more improvement since %d epochs. Training stopped.' % earlyStopping)
      break


def validate(model, loader):
    "validate NN"
    #print('Validate NN')
    loader.validationSet()
    numCharErr = 0
    numCharTotal = 0
    numWordOK = 0
    numWordTotal = 0
    while loader.hasNext():
        iterInfo = loader.getIteratorInfo()
        #print('Batch:', iterInfo[0],'/', iterInfo[1])
        batch = loader.getNext()
        (recognized, _) = model.inferBatch(batch)
        
        #print('Ground truth -> Recognized')    
        for i in range(len(recognized)):
            numWordOK += 1 if batch.gtTexts[i] == recognized[i] else 0
            numWordTotal += 1
            dist = editdistance.eval(recognized[i], batch.gtTexts[i])
            numCharErr += dist
            numCharTotal += len(batch.gtTexts[i])
            #print('[OK]' if dist==0 else '[ERR:%d]' % dist,'"' + batch.gtTexts[i] + '"', '->', '"' + recognized[i] + '"')
    
    # print validation result
    charErrorRate = numCharErr / numCharTotal
    wordAccuracy = numWordOK / numWordTotal
    #print('Character error rate: %f%%. Word accuracy: %f%%.' % (charErrorRate*100.0, wordAccuracy*100.0))
    return charErrorRate


def infer(model, fnImg):
    "recognize text in image provided by file path"
    img = preprocess(cv2.imread(fnImg, cv2.IMREAD_GRAYSCALE), Model.imgSize)
    batch = Batch(None, [img])
    (recognized, probability) = model.inferBatch(batch, True)
    st.image(fnImg, caption='Image containing word')
    st.title("Predicted word : ")
    st.title(recognized[0])
    st.title("Accuracy : ")
    st.title(probability[0])


def main():
    "main function"
    # optional command line args
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', help='train the NN', action='store_true')
    parser.add_argument('--validate', help='validate the NN', action='store_true')
    parser.add_argument('--beamsearch', help='use beam search instead of best path decoding', action='store_true')
    parser.add_argument('--wordbeamsearch', help='use word beam search instead of best path decoding', action='store_true')
    parser.add_argument('--dump', help='dump output of NN to CSV file(s)', action='store_true')

    args = parser.parse_args()

    decoderType = DecoderType.BestPath
    if args.beamsearch:
        decoderType = DecoderType.BeamSearch
    elif args.wordbeamsearch:
        decoderType = DecoderType.WordBeamSearch

    # train or validate on IAM dataset  
    if args.train or args.validate:
        # load training data, create TF model
        loader = DataLoader(FilePaths.fnTrain, Model.batchSize, Model.imgSize, Model.maxTextLen)

        # save characters of model for inference mode
        open(FilePaths.fnCharList, 'w').write(str().join(loader.charList))
        
        # save words contained in dataset into file
        open(FilePaths.fnCorpus, 'w').write(str(' ').join(loader.trainWords + loader.validationWords))

        # execute training or validation
        if args.train:
            model = Model(loader.charList, decoderType)
            train(model, loader)
        elif args.validate:
            model = Model(loader.charList, decoderType, mustRestore=True)
            validate(model, loader)

    # infer text on test image
    else:
        #print(open(FilePaths.fnAccuracy).read())
        model = Model(open(FilePaths.fnCharList).read(), decoderType, mustRestore=True, dump=args.dump)
        infer(model,FilePaths.path)

if st.button('Predict'):
  main()