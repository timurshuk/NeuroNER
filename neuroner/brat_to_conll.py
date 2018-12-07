# -*- coding: utf-8 -*-
import codecs
import glob
import json
import os

from pycorenlp import StanfordCoreNLP
import spacy

from neuroner import utils_nlp
from preprocessor import *

def get_sentences_and_tokens_custom(text, entities):
    """ use tokenizer that will take al symbols apart from the words
    and assign to each character it's label and position coordinates
    """
    i = 0
    sentences = []
    processor = Preprocessor()
    start_end_entities = [(entity['start'],entity['end'],entity['type']) for entity in entities]

    for ind,word in enumerate(processor.preprocess(text)):    
        is_entity=False
        start_index = text[i:].find(word)+i
        end_index = start_index + len(word)
        i = end_index
        for x in start_end_entities:
            if start_index in range(x[0],x[1]):
                is_entity=True
                sentences.append({'start': start_index,'end': end_index, 'label': x[2], 'text': word})
        if is_entity==False:
            sentences.append({'start': start_index,'end': end_index, 'label': 'O', 'text': word})
    return sentences

def get_entities_from_brat(text_filepath, annotation_filepath, verbose=False):
    # load text
    with codecs.open(text_filepath, 'r', 'UTF-8') as f:
        text =f.read()
    if verbose: print("\ntext:\n{0}\n".format(text))

    # parse annotation file
    entities = []
    with codecs.open(annotation_filepath, 'r', 'UTF-8') as f:
        for line in f.read().splitlines():
            anno = line.split()
            id_anno = anno[0]
            # parse entity
            if id_anno[0] == 'T':
                entity = {}
                entity['id'] = id_anno
                entity['type'] = anno[1]
                entity['start'] = int(anno[2])
                entity['end'] = int(anno[3])
                entity['text'] = ' '.join(anno[4:])
                if verbose:
                    print("entity: {0}".format(entity))
                # Check compatibility between brat text and anootation
                if utils_nlp.replace_unicode_whitespaces_with_ascii_whitespace(text[entity['start']:entity['end']]) != \
                    utils_nlp.replace_unicode_whitespaces_with_ascii_whitespace(entity['text']):
                    print("Warning: brat text and annotation do not match.")
                    print("\ttext: {0}".format(text[entity['start']:entity['end']]))
                    print("\tanno: {0}".format(entity['text']))
                # add to entitys data
                entities.append(entity)
    if verbose: print("\n\n")
    
    return text, entities

def check_brat_annotation_and_text_compatibility(brat_folder):
    '''
    Check if brat annotation and text files are compatible.
    '''
    dataset_type =  os.path.basename(brat_folder)
    print("Checking the validity of BRAT-formatted {0} set... ".format(dataset_type), end='')
    text_filepaths = sorted(glob.glob(os.path.join(brat_folder, '*.txt')))
    for text_filepath in text_filepaths:
        base_filename = os.path.splitext(os.path.basename(text_filepath))[0]
        annotation_filepath = os.path.join(os.path.dirname(text_filepath), base_filename + '.ann')
        # check if annotation file exists
        if not os.path.exists(annotation_filepath):
            raise IOError("Annotation file does not exist: {0}".format(annotation_filepath))
        text, entities = get_entities_from_brat(text_filepath, annotation_filepath)
    print("Done.")

def brat_to_conll(input_folder, output_filepath):
    '''
    Assumes '.txt' and '.ann' files are in the input_folder.
    Checks for the compatibility between .txt and .ann at the same time.
    '''
    verbose = False
    dataset_type =  os.path.basename(input_folder)
    print("Formatting {0} set from BRAT to CONLL... ".format(dataset_type), end='')
    text_filepaths = sorted(glob.glob(os.path.join(input_folder, '*.txt')))
    output_file = codecs.open(output_filepath, 'w', 'utf-8')
    for text_filepath in text_filepaths:
        #output_file.write('-DOCSTART- -X- -X- O\n\n')

        base_filename = os.path.splitext(os.path.basename(text_filepath))[0]
        annotation_filepath = os.path.join(os.path.dirname(text_filepath), base_filename + '.ann')
        # create annotation file if it does not exist
        if not os.path.exists(annotation_filepath):
            codecs.open(annotation_filepath, 'w', 'UTF-8').close()

        text, entities = get_entities_from_brat(text_filepath, annotation_filepath)
        entities = sorted(entities, key=lambda entity:entity["start"])
        
        # run custom tokenizer
        sentences = get_sentences_and_tokens_custom(text,entities)
        
        inside = False
        previous_token_label = 'O'
        for token in sentences:
            token['label'] = 'O'
            for entity in entities:
                if entity['start'] <= token['start'] < entity['end'] or \
                   entity['start'] < token['end'] <= entity['end'] or \
                   token['start'] < entity['start'] < entity['end'] < token['end']:

                    token['label'] = entity['type'].replace('-', '_') # Because the ANN doesn't support tag with '-' in it

                    break
                elif token['end'] < entity['start']:
                    break
                    
            if len(entities) == 0:
                entity={'end':0}
            if token['label'] == 'O':
                gold_label = 'O'
                inside = False
            elif inside and token['label'] == previous_token_label:
                gold_label = 'I-{0}'.format(token['label'])
            else:
                inside = True
                gold_label = 'B-{0}'.format(token['label'])
            if token['end'] == entity['end']:
                inside = False
            previous_token_label = token['label']
            if verbose: print('{0} {1} {2} {3} {4}\n'.format(token['text'], base_filename, token['start'], token['end'], gold_label))
            output_file.write('{0} {1} {2} {3} {4}\n'.format(token['text'], base_filename, token['start'], token['end'], gold_label))
        if verbose: print('\n')
        output_file.write('\n')

    output_file.close()
    print('Done.')
