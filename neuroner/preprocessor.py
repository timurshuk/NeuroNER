import re,random

dirt_regexp = re.compile('(\n[^\S\n]*.[^\S\n]*)+\n')
repeating_new_lines_regexp = re.compile('\n{3,}')
repeating_spaces_regexp = re.compile('[^\S\n]{3,}')
tags_regexp = re.compile('\[(image|bookmark): [^\]\[]*\]')
repeating_punctuation_regexp = re.compile(
    '(([^\w\s]|_)([^\w]|_)+([^\w\s]|_))'
)


class Preprocessor:
    
    def check_none(self,value):
        if value is None: 
            return ''
        else: return value

    def random_colon(self,word):
        if word != "":
            return word + random.choice(["",":"])
        else: return word
        
    def preprocess(self, text):
        text = dirt_regexp.sub('\n', text)
        text = repeating_new_lines_regexp.sub('\n\n', text)
        text = repeating_spaces_regexp.sub('  ', text)
        text = tags_regexp.sub('', text)
        text = repeating_punctuation_regexp.sub('\\2\\4', text)
        split_by_digits = [x for x in re.split('(\d+)', text) if x.strip() != '']
        split_by_letter = [x.strip() for x in re.split('(\W)', ' '.join(split_by_digits)) if x.strip() != '']
        return split_by_letter

    def get_tags(self,field,entity,tag):
        """ Preprocesses field and entity and constructs tags.
        Keyword arguments:
        field -- a sentence with entity (str)
        entity -- entity phrase (str)
        tag -- special tag (str)
        """
        if field == '' or entity == '': return [], []
        tokenized_field = self.preprocess(field)
        tokenized_entity = self.preprocess(entity)

        tags = []
        entity_start = None
        entity_end = None
        
        for ind, word in enumerate(tokenized_field):
            if tokenized_field[ind:ind+len(tokenized_entity)] == tokenized_entity and not entity_start:
                entity_start = ind
                entity_end = ind+len(tokenized_entity)
            
            if entity_start != None:
                if ind in range(entity_start, entity_end):
                    tags.append(tag)
                else:
                    tags.append('O')
            else:
                tags.append('O')        
        
        bio_tags = []
        
        for ind,tag in enumerate(tags):
            if tag != 'O' and tags[ind-1] == 'O' or tag!='O' and ind == 0: bio_tags.append('B-' + tag)
            elif tag != 'O' and tags[ind-1] != 'O': bio_tags.append('I-' + tag)
            else: bio_tags.append(tag)
        
        return tokenized_field, bio_tags