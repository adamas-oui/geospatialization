from bs4 import BeautifulSoup as bs
import beta_code
from cltk import NLP
import requests 
import time
import folium
from math import *


content = []
with open("thuc.xml", "r") as fh:
    content = fh.readlines()
    content = "".join(content)
    bs_content = bs(content, "lxml")
beta_text = []
for line in bs_content.findAll("p"):
    beta_text.append(line.text)
# for line in beta_text[:3]:
#     print(line)

text = []
for line in beta_text:
    text.append(beta_code.beta_code_to_greek(line))
# for line in text[:2]:
#     print(line)
one_string_text = ''.join(text)
# print(one_string_text[:2000])

cltk_nlp_grc = NLP(language='grc')
cltk_doc_grc = cltk_nlp_grc.analyze(text=one_string_text)
# print(cltk_doc_grc.lemmata[:254])
# print(cltk_doc_grc.pos[:254])
# for i in range(2000):
#         print(cltk_doc_grc.lemmata[i], cltk_doc_grc.pos[i])
print("==== the end of tokenization ====")


# GEONAMES
def search_geonames(name, style="medium", exact=False, max_rows=10, fuzz=1, feature_classes=None,
                feature_codes=None, countries=None, state_code=None, retry_attempts=0):
    """
    get the raw response back from GeoNames as a dictionary

    :param fuzz:
    :param state_code:
    :param countries:
    :param feature_codes:
    :param exact:
    :param name:
    :param feature_classes:
    :param max_rows:
    :param style: API parameter that determines fields returned
    :param retry_attempts: how many times to retry the request if it fails
    :return:
    """
    # pause execution to prevent dos'ing the GeoNames server
    time.sleep(0.3)

    # default parameters
    params = {
        'username': 'data_lab',
        'style': style,
        'name': name,
        'isNameRequired': True,
        'inclBbox': True,
        'type': 'json',
        'fuzzy': fuzz,
        'maxRows': max_rows
    }

    if fuzz < 1:
        params['isNameRequired'] = False

    if not exact:
        params['name'] = name
    else:
        params['name_equals'] = name

    if feature_codes is not None:
        params['featureCode'] = feature_codes

    if feature_classes is not None:
        params['featureClass'] = feature_classes

    if countries is not None:
        params['country'] = countries

    if state_code is not None:
        params['adminCode1'] = state_code

    gn_url = 'http://api.geonames.org/search'  # baseurl for geonames search

    try:
        response = requests.get(gn_url, params=params, timeout=None)
    except requests.exceptions.Timeout as e:
        # if specified in the arguments, retry the API call on request timeout
        print(e)
        if retry_attempts > 0:
            retry_attempts -= 1
            return search_name(name, retry_attempts=retry_attempts)
        else:
            raise Exception('Timeout after specified retries.')

    if response.status_code == 200:
        return response.json()
    
    # for any response where the status code is not 200 ('success') retry the API call
    if retry_attempts > 0:
        retry_attempts -= 1
        return search_name(name, retry_attempts=retry_attempts)
    else:
        raise Exception('Status code: ' + str(response.status_code))

#PERIPLEO

def search_peripleo(name, fuzzy=False, datasets=('pleiades'), from_date=-3000, to_date=1000, retry_attempts=0):
    """
    get the raw response back from peripleo as a dictionary. look here for more details: https://github.com/pelagios/peripleo/blob/main/README.md
    :param name: place name to search
    :param fuzzy: whether a fuzzy search should be performed
    :param datasets: which datasets should be included in the search
    :param from_date: start date for search
    :param to_date: end date for search
    :param retry_attempts: how many times to retry the request if it fails
    :return:
    """
    # pause execution to prevent dos'ing the GeoNames server
    time.sleep(0.3)

    # default parameters
    params = {
        'query': name,
        'types': 'place',
        'from': from_date,
        'to': to_date,
        'datasets': datasets
    }

    if fuzzy:
        params['query'] = params['query'] + '~'

    gz_url = 'http://peripleo.pelagios.org/peripleo/search'  # baseurl for peripleo search

    try:
        response = requests.get(gz_url, params=params, timeout=None)
    except requests.exceptions.Timeout as e:
        # if specified in the arguments, retry the API call on request timeout
        print(e)
        if retry_attempts > 0:
            retry_attempts -= 1
            return search_name(name, retry_attempts=retry_attempts)
        else:
            raise Exception('Timeout after specified retries.')

    if response.status_code == 200:
        return response.json()
    
    # for any response where the status code is not 200 ('success') retry the API call
    if retry_attempts > 0:
        retry_attempts -= 1
        return search_name(name, retry_attempts=retry_attempts)
    else:
        raise Exception('Status code: ' + str(response.status_code))

def display_geoname(place):
    """
    parse json response from geonames API (medium response for each place)
    :param place:
    :return:
    """

    fcl = place['fcl']

    if fcl == 'P':
        if 'countryCode' in place:
            # populated place
            if place['countryCode'] == 'US':
                return place['name'] + ', ' + place['adminCode1'] + ' (US city)'

            else:
                return place['name'] + ' (city, country: ' + place['countryCode'] + ')'
        else:
            print('Populated place with no country code')
            print(place)

    elif fcl == 'A':
        # admin
        fcode = place['fcode']
        if fcode == 'PCLI':
            return place['name'] + ' (country)'

        if 'countryCode' in place:
            if place['countryCode'] == 'US':
                if fcode == 'ADM1':
                    return place['name'] + ' (US state)'
                elif fcode == 'ADM2':
                    return place['name'] + ', ' + place['adminCode1'] + ' (US county)'
                elif fcode == 'ZN':
                    return place['name'] + ' (US Zone)'
                else:
                    if 'adminCode1' not in place:
                        print(place)
                        return 'unrecognized feature type'

                    return place['name'] + ', ' + place['adminCode1'] + ' (US admin level: ' + fcode + ')'
            else:
                adminlevel = place['fcodeName']
                if fcode == 'ADM1':
                    adminlevel = 'admin 1'
                elif fcode == 'ADM2':
                    adminlevel = 'admin 2'
                elif fcode == 'ADM3':
                    adminlevel = 'admin 3'
                elif fcode == 'ADM4':
                    adminlevel = 'admin 4'
                elif fcode == 'ADM5':
                    adminlevel = 'admin 5'
                return place['name'] + ' (' + adminlevel + ', country: ' + place['countryCode'] + ')'
    elif fcl == 'L' and place['toponymName'] == 'Earth':
        # special value for Earth
        return place['toponymName'] + ' (world wide)'

    else:
        # H: water bodies, L: parks, area..., T: mountain, hill..., S: spot, building
        if 'countryCode' in place:
            descriptor = place['fcodeName'] + ', country: ' + place['countryCode']
        else:
            descriptor = place['fcodeName']
        return place['toponymName'] + ' (' + descriptor + ')'
        
#using Thuc 7.1
pos_tags = ['DET', 'ADV', 'PROPN', 'CCONJ', 'DET', 'PROPN', 'ADP', 'DET', 'PROPN', 'SCONJ', 'VERB', 'DET', 'NOUN', 'VERB', 'ADP', 'NOUN', 'DET', 'NOUN', 'CCONJ', 'VERB', 'ADJ', 'ADV', 'SCONJ', 'ADV', 'ADV', 'ADV', 'VERB', 'DET', 'PROPN', 'VERB', 'ADV', 'ADV', 'ADV', 'ADJ', 'CCONJ', 'ADP', 'DET', 'PROPN', 'NOUN', 'NOUN', 'VERB', 'VERB', 'CCONJ', 'ADV', 'ADP', 'ADJ', 'VERB', 'DET', 'PROPN', 'VERB', 'VERB', 'ADV', 'ADV', 'ADP', 'ADJ', 'ADP', 'PROPN', 'ADJ', 'VERB', 'CCONJ', 'DET', 'CCONJ', 'DET', 'CCONJ', 'NOUN', 'ADJ', 'VERB', 'PRON', 'ADV', 'VERB', 'ADP', 'NOUN', 'VERB', 'CCONJ', 'VERB', 'PRON', 'ADP', 'DET', 'PROPN', 'VERB', 'ADV', 'CCONJ', 'CCONJ', 'DET', 'ADJ', 'NUM', 'NOUN', 'ADV', 'VERB', 'ADP', 'DET', 'PROPN', 'PRON', 'DET', 'PROPN', 'ADV', 'VERB', 'PRON', 'ADP', 'NOUN', 'AUX', 'VERB', 'VERB', 'ADV', 'DET', 'NOUN', 'DET', 'VERB', 'ADP', 'DET', 'NOUN', 'CCONJ', 'VERB', 'PROPN', 'CCONJ', 'PROPN', 'VERB', 'ADP', 'PROPN', 'SCONJ', 'ADV', 'ADV', 'AUX', 'DET', 'CCONJ', 'NOUN', 'VERB', 'VERB', 'CCONJ', 'ADJ', 'CCONJ', 'VERB', 'CCONJ', 'DET', 'ADP', 'DET', 'NOUN', 'DET', 'NOUN', 'NOUN', 'PRON', 'ADV', 'VERB', 'NOUN', 'VERB', 'NOUN', 'ADV', 'NOUN', 'VERB', 'ADP', 'PROPN', 'CCONJ', 'DET', 'NOUN', 'VERB', 'VERB', 'VERB', 'NOUN', 'ADP', 'DET', 'ADJ', 'SCONJ', 'VERB', 'ADV', 'DET', 'PRON', 'VERB', 'NOUN', 'ADV', 'ADJ', 'CCONJ', 'DET', 'NOUN', 'CCONJ', 'DET', 'NOUN', 'ADV', 'PRON', 'ADJ', 'ADJ', 'VERB', 'ADJ', 'AUX', 'DET', 'CCONJ', 'PROPN', 'ADV', 'VERB', 'PRON', 'DET', 'DET', 'NOUN', 'NOUN', 'DET', 'CCONJ', 'AUX', 'ADV', 'ADJ', 'DET', 'NOUN', 'NOUN', 'VERB', 'DET', 'PROPN', 'ADP', 'PROPN', 'ADV', 'VERB', 'VERB', 'CCONJ', 'DET', 'ADV', 'PROPN', 'VERB', 'DET', 'CCONJ', 'NOUN', 'NOUN', 'CCONJ', 'NOUN', 'DET', 'NOUN', 'ADJ', 'NOUN', 'NOUN', 'ADV', 'NOUN', 'CCONJ', 'ADJ', 'ADJ', 'ADJ', 'CCONJ', 'NOUN', 'NUM', 'CCONJ', 'NOUN', 'CCONJ', 'DET', 'ADJ', 'CCONJ', 'NOUN', 'CCONJ', 'NOUN', 'ADJ', 'NOUN', 'CCONJ', 'ADP', 'ADJ', 'DET', 'NOUN', 'VERB', 'ADP', 'DET', 'PROPN']

tokens = ['ὁ', 'δέ', 'Γύλιππος', 'καί', 'ὁ', 'Πυθήν', 'ἐκ', 'ὁ', 'Τρράντος', 'ἐπεί', 'ἐπισκευγαΐζω', 'ὁ', 'ναύς', 'παροπλέω', 'εἰς', 'Λοκρός', 'ὁ', 'Ἐπιζεφυργους', 'καί', 'πυνθάνομαι', 'σαφόστερος', 'ἤδη', 'ὅτι', 'οὐ', 'παντελῶς', 'πω', 'ἀποτειχίζω', 'ὁ', 'Συρρκουσαῦ', 'εἴσειμι', 'ἀλλ', '̓', 'ἔτι', 'οἷος', 'τε', 'κατά', 'ὁ', 'Ἐπιπολή', 'στρατιά', 'ἀφικομόνος', 'εἰσέρχομαι', 'βουλεύω', 'εἴτ', '̓', 'ἐν', 'δεξιός', 'λαμβάνω', 'ὁ', 'Σικελώα', 'διακινδυνεύω', 'εἰσπλεύω', 'εἴτ', '̓', 'ἐν', 'ἀριστερός', 'εἰς', 'Ἱμόρα', 'πρῶτος', 'πλέω', 'καί', 'αὐτός', 'τε', 'ἐκεῖδος', 'καί', 'στρατιά', 'ἄλλος', 'προσλαβρνέω', 'ὅς', 'ἄν', 'πεωθω', 'κατά', 'γῆ', 'ἔρχομαι', 'καί', 'δοκέω', 'αὐτός', 'ἐπί', 'ὁ', 'Ἱμυραί', 'πλέω', 'ἄλλως', 'τε', 'καί', 'ὁ', 'Ἀττικός', 'τέσσυρος', 'ναῦς', 'οὔπω', 'πάρειμι', 'ἐν', 'ὁ', 'Ῥηγυσύς', 'ὅς', 'ὁ', 'Νικραί', 'ὅμως', 'πυνθάνομαι', 'αὐτός', 'ἐν', 'Λοκρός', 'εἰμί', 'ἀποστέλλω', 'φθόνω', 'δέ', 'ὁ', 'φυλακή', 'οὗτος', 'περαιόω', 'διά', 'ὁ', 'πορθμούς', 'καί', 'ἔχω', 'Ῥῆγυον', 'καί', 'Μεσσυνα', 'ἀφικνέομαι', 'εἰς', 'Ἱμόρα', '.', 'ἐκεῖ', 'δέ', 'εἰμί', 'ὁ', 'τε', 'ὅμεραδος', 'πείθω', 'ξυμπολέω', 'καί', 'αὐτός', 'τε', 'ἕπομαι', 'καί', 'ὁ', 'ἐκ', 'ὁ', 'ναῦς', 'ὁ', 'σφέτωρος', 'ναύτης', 'ὅσος', 'μή', 'ἔχω', 'ὅπλον', 'παρέχω', 'οὖς', 'γάρ', 'ναῦς', 'ἀνουλύω', 'ἐν', 'Ἱμόραζα', 'καί', 'ὁ', 'Σελινούντης', 'πομπάω', 'κωλεύω', 'ἀπαντάω', 'πανστρατιά', 'εἰς', 'τὶς', 'χωρύς', '.', 'πομπέω', 'δέ', 'τὶς', 'αὐτός', 'ὑπόχω', 'στρατιά', 'οὐ', 'πολύς', 'καί', 'ὁ', 'Γελῷος', 'καί', 'ὁ', 'Σικελός', 'τινές,', 'ὁ', 'πολύς', 'προθυμότερος', 'προσχωρέω', 'ἑτοίμος', 'εἰμί', 'ὁ', 'τε', 'Ἀρχωνρδος', 'νεωστί', 'θνῄκω', 'ὅς', 'ὁ', 'οὗτος', 'Σικελός', 'βασιλεύς', 'τὶς', 'καί', 'εἰμί', 'οὐ', 'ἀδύνατος', 'ὁ', 'Ἀθηναῦος', 'φίλος', 'γιγνώσκω', 'ὁ', 'Γυλύππος', 'ἐκ', 'Λακεδαομονὶ', 'προθύμως', 'δοκέω', 'ἥκω', 'καί', 'ὁ', 'μέν', 'Γύλιππος', 'ἀναλαμβάνω', 'ὁ', 'τε', 'σφέτωρος', 'ναύτης', 'καί', 'ἐπιβάτης', 'ὁ', 'ὡπλισμόνος', 'ἑπτάκοσυς', 'μυλιστής', 'ὅμεραδος', 'δέ', 'ὁπλότης', 'καί', 'ψιλός', 'ξυναμφότυρος', 'χίλυος', 'καί', 'ἱπποή', 'ἑκατόν', 'καί', 'Σελινοῦντων', 'τέ', 'τὶς', 'ψιλός', 'καί', 'ἱπποή', 'καί', 'Γελῷος', 'ὀλῳγουῖς', 'Σικελός', 'τε', 'εἰς', 'χίλυος', 'ὁ', 'πινταῖος', 'χράω', 'πρός', 'ὁ', 'Συράκουσαι']

#merge the two lists
matched = zip(tokens, pos_tags)

#filter for proper nouns
proper_nouns = [i[0] for i in matched if i[1] == 'PROPN']

# print(proper_nouns)

#### match all propns against geonames gazetteer ####
# geocode_results = []
# for i in proper_nouns:
#     print(f'matching {i} against GeoNames gazetteer...')
#     # restricting search to basic feature classes and country = Greece. You may not want to restrict to Greece only if your text may present places in other countries
#     geocode_results.append({'token': i, 'results': search_geonames(i, exact=True, feature_classes=['P','A','L','H','T'], countries='GR')})

# print(geocode_results)

#### match all propns against Peropleo gazetteer ####

peripleo_results = []
for i in proper_nouns:
    print(f'matching {i} against peripleo (Pleiades) gazetteer...')
    # search has default time bounds and default dataset is Pleiades. look at the code for details
    peripleo_results.append({'token': i, 'results': search_peripleo(i, fuzzy=True)})
    
# print(peripleo_results)
peripleo_places = [{'token': i['token'], 'place': i['results']['items'][0]} for i in peripleo_results if len(i['results']['items']) > 0]
print(peripleo_places)

# #map the found places 
# def bbox_center(bbox):
#     """
#     give the centroid of a bounding box
#     ex: in: bbox = 'geo_bounds': {'min_lon': 31.133358, 'max_lon': 31.133358, 'min_lat': 30.12311, 'max_lat': 30.12311}
#         out: [center_lat, center_lon]
#     """
#     def center_point(min_p, max_p):
#         return (max_p - min_p)/2 + min_p
#     return [center_point(bbox['min_lat'], bbox['max_lat']), center_point(bbox['min_lon'], bbox['max_lon'])]
# 
# def merge_bounds(bbox1, bbox2):
#     return {'min_lon': min(bbox1['min_lon'], bbox2['min_lon']), 
#             'max_lon': max(bbox1['max_lon'], bbox2['max_lon']),
#             'min_lat': min(bbox1['min_lat'], bbox2['min_lat']), 
#             'max_lat': max(bbox1['max_lat'], bbox2['max_lat'])}
# 
# pp = peripleo_places[0]['place']
# 
# # find bounding box of all places
# bbox = None
# for i in peripleo_places:
#     if bbox is None:
#         bbox = i['place']['geo_bounds']
#     else:
#         bbox = merge_bounds(bbox, i['place']['geo_bounds'])
# 
# # reformat for folium, add buffer
# bbox = [(bbox['min_lat'] - 1, bbox['min_lon'] - 1), (bbox['max_lat'] + 1, bbox['max_lon'] + 1)]        
# 
# peripleo_map = folium.Map()
# 
# for i in peripleo_places:
#     center = bbox_center(i['place']['geo_bounds'])
#     popup = f'<h2>{i["token"]}</h2><br/><i>{i["place"]["title"]}</i><br/><a href="{i["place"]["identifier"]}">{i["place"]["identifier"]}</a>'
#     # add a marker foor the place
#     folium.Marker(center, popup=popup).add_to(peripleo_map)
# 
# folium.FitBounds(bbox).add_to(peripleo_map)
# 
# print(peripleo_map)











