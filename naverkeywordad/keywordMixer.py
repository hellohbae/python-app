#-*- coding: utf-8 -*-
import itertools
import json
import airtable

AIRTABLE_API_KEY = 'keygLnwALvJEd9AVc'
AIRTABLE_BASE_URL = 'https://api.airtable.com/v0/appFAQcgBJy6jIXSw'
MIN_ADJECTIVE_COMBINATION = 1
MAX_ADJECTIVE_COMBINATION = 2


def classify_by_keyword_group(records):
    list_by_keyword_group = [ [records[0]] ]
    for i in range(1, len(records)):
        not_found = True
        for group in list_by_keyword_group:
            if group[0]['keyword_group_name']==records[i]['keyword_group_name']:
                group.append(records[i])
                not_found = False
                continue
        if not_found:
            list_by_keyword_group.append([ records[i] ])

    return list_by_keyword_group

def make_combination_by_list_1(adjective_list_by_keyword_group, number_of_adjective):
    adjective_group_combi_list = list(map(list, itertools.combinations(adjective_list_by_keyword_group, number_of_adjective)))
    adjective_keyword_group_names_list = []
    for each_adjective_group_combi in adjective_group_combi_list:
        each_adjective_keyword_group_name_list = []
        for adjective_group in each_adjective_group_combi:
            each_adjective_keyword_group_name_list.append(adjective_group[0]['keyword_group_name'])
        each_adjective_keyword_group_name_list.sort()
        adjective_keyword_group_names_list.append(each_adjective_keyword_group_name_list)

    return adjective_group_combi_list, adjective_keyword_group_names_list

def make_combination_by_list_2(each_adjective_group_combi, adjective_group_names, each_essential_list_by_keyword_group):
    combi_list = list(map(list, itertools.product(*each_adjective_group_combi, each_essential_list_by_keyword_group)))
    ad_group_name_list = adjective_group_names + [each_essential_list_by_keyword_group[0]['keyword_group_name']]
    data = {
        'ad_group_name': '_'.join(ad_group_name_list),
        'combi_list': combi_list,
        'essential_keyword_group_id': each_essential_list_by_keyword_group[0]['keyword_group_id']
    }
    for i in range(len(adjective_group_names)):
        key = 'adjective_keyword_group_id_'+str(i+1)
        data[key] = each_adjective_group_combi[i][0]['keyword_group_id']
        
    return data

def make_new_keyword(adjective_list_by_keyword_group, essential_list_by_keyword_group, number_of_adjective, airtable, new_word_list):
    adjective_group_combi_list, adjective_keyword_group_names_list = make_combination_by_list_1(adjective_list_by_keyword_group, number_of_adjective)
    data_list = []
    if not adjective_group_combi_list:
        for each_essential_list_by_keyword_group in essential_list_by_keyword_group:
            data_list.append(make_combination_by_list_2([],[],each_essential_list_by_keyword_group))
    else:
        for each_essential_list_by_keyword_group in essential_list_by_keyword_group:
            for i in range(len(adjective_group_combi_list)):
                data_list.append(make_combination_by_list_2(adjective_group_combi_list[i], adjective_keyword_group_names_list[i], each_essential_list_by_keyword_group))

    all_keyword_list = []
    for group_data in data_list:
        ad_group_record_id = airtable.get_ad_group(group_data, number_of_adjective)
        for word_list in group_data['combi_list']:
            found = False
            for word in word_list:
                for new_word in new_word_list:
                    if word == new_word:
                        found = True
                        break
                if found:
                    break
            if not found:
                continue
            different_order_word_list = itertools.permutations(word_list)
            for keyword_list in different_order_word_list:
                keyword_str = ''
                for keyword in keyword_list:
                    keyword_str += keyword['word'] + ' '
                keyword_str.strip()

                data2 = {
                    'ad_group_id': [ad_group_record_id],
                    'keyword': keyword_str
                }
                for i in range(number_of_adjective+1):
                    key = 'word_id_'+str(i+1)
                    data2[key] = [keyword_list[i]['record_id']]
                all_keyword_list.append(data2)

    return all_keyword_list

if __name__=='__main__':
    airtable = airtable.Airtable(AIRTABLE_API_KEY, AIRTABLE_BASE_URL)
    response = airtable.get_request(airtable.get_base_url()+'/words')
    old_adjective_records = []
    old_essential_records = []
    for record in response['records']:
        linked_record_id = record['fields']['keyword_group_id'][0]
        response2 = airtable.get_request(airtable.get_base_url()+'/keyword_group/'+linked_record_id)
        record['fields']['keyword_group_name'] = response2['fields']['name']
        record['fields']['record_id'] = record['id']
        if response2['fields']['classification']=='adjective':
            old_adjective_records.append(record['fields'])
        elif response2['fields']['classification']=='essential':
            old_essential_records.append(record['fields'])

    response = airtable.get_request(airtable.get_base_url()+'/new_words')
    new_adjective_records = []
    new_essential_records = []
    for record in response['records']:
        linked_record_id = record['fields']['keyword_group_id'][0]
        response2 = airtable.get_request(airtable.get_base_url()+'/keyword_group/'+linked_record_id)
        data = {
            'word': record['fields']['word'],
            'keyword_group_id': record['fields']['keyword_group_id']
        }
        words_record = airtable.post_request(airtable.get_base_url()+'/words', json.dumps({"fields": data}))
        airtable.delete_request(airtable.get_base_url()+'/new_words/'+record['id'])
        record['fields']['keyword_group_name'] = response2['fields']['name']
        record['fields']['record_id'] = words_record['id']
        if response2['fields']['classification']=='adjective':
            new_adjective_records.append(record['fields'])
        elif response2['fields']['classification']=='essential':
            new_essential_records.append(record['fields'])

    minimum_number_of_adjective = MIN_ADJECTIVE_COMBINATION
    maximum_number_of_adjective = MAX_ADJECTIVE_COMBINATION

    essential_list_by_keyword_group = classify_by_keyword_group(new_essential_records+old_essential_records)
    adjective_list_by_keyword_group = classify_by_keyword_group(new_adjective_records+old_adjective_records)
    new_word_list = new_essential_records + new_adjective_records

    for number_of_adjective in range(minimum_number_of_adjective, maximum_number_of_adjective+1):
        if len(adjective_list_by_keyword_group) < number_of_adjective or len(essential_list_by_keyword_group) < 1:
            continue

        keyword_list = make_new_keyword(adjective_list_by_keyword_group, essential_list_by_keyword_group, number_of_adjective, airtable, new_word_list)

        for keyword in keyword_list:
            airtable.post_request(airtable.get_base_url()+'/keywords', json.dumps({"fields": keyword}))
          
