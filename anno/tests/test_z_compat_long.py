import json
import os

import pytest
from anno.json_models import AnnoJS, Catcha
from anno.models import Anno
from consumer.models import Consumer
from django.test import Client
from django.urls import reverse

from .conftest import make_encoded_token, make_jwt_payload, readfile_into_jsonobj


#
# TODO: id in body is ignored and a new one is created
#
@pytest.mark.skip('broken')
@pytest.mark.django_db
def test_long_annotatorjs():
    here = os.path.abspath(os.path.dirname(__file__))
    # filename = os.path.join(here, 'annojs_3K_sorted.json')
    # filename = os.path.join(here, 'annojs_HxAT101.json')
    filename = os.path.join(here, 'annojs_sample_1.json')
    sample = readfile_into_jsonobj(filename)

    created_list = []
    failed_to_create = []
    client = Client()
    c = Consumer._default_manager.create()

    no_media = []
    for js in sample:

        if 'media' not in js:
            no_media.append(js['id'])
            failed_to_create.append(js['id'])
            continue

        # prep and remove insipient props for compare easiness
        # js['id'] = str(js['id'])
        js['uri'] = str(js['uri'])
        del(js['archived'])
        del(js['deleted'])
        if 'citation' in js:
            del(js['citation'])
        if 'quote' in js and not js['quote']:
            del(js['quote'])
        if 'parent' not in js:
            js['parent'] = '0'
        if 'contextId' not in js:
            js['contextId'] = 'unknown'
        if 'collectionId' not in js:
            js['collectionId'] = 'unknown'

        payload = make_jwt_payload(
            apikey=c.consumer, user=js['user']['id'])
        token = make_encoded_token(c.secret_key, payload)

        url = reverse('compat_create')
        response = client.post(
            url, data=json.dumps(js),
            HTTP_X_ANNOTATOR_AUTH_TOKEN=token,
            content_type='application/json')

        '''
        if response.status_code != 200:
            print('failed to create js({}): {}\n{}'.format(
                js['id'], response.content,
                json.dumps(js, sort_keys=True, indent=4)))
            failed_to_create.append(js['id'])

            assert response.status_code == 200

        else:
            resp = json.loads(response.content)
        '''
        assert response.status_code == 200
        resp = json.loads(response.content)

    how_many = len(no_media)
    if how_many > 0:
        print('******* found ({}) annotations with no_media: {}'.format(
            len(no_media), no_media))


    # able to insert all annotatorjs! now comparing
    counter = 0
    pulled_from_db = 0
    for js in sample:
        if js['id'] in failed_to_create:
            print('skipping not created anno({})'.format(js['id']))
            continue  # skip if could not create

        created_anno = Anno._default_manager.get(pk=js['id'])
        pulled_from_db += 1
        created_js = AnnoJS.convert_from_anno(created_anno)

        if AnnoJS.are_similar(js, created_js):
            catcha = AnnoJS.convert_to_catcha(js)
            assert Catcha.are_similar(catcha, created_anno.serialized)
        else:
            # sometimes the tags are repeated or not present!
            js['tags'] = list(set(js['tags'])) if 'tags' in js else []
            created_js['tags'] = created_js['tags'] if 'tags' in created_js else []
            if AnnoJS.are_similar(js, created_js):
                print('---------- AnnoJS similar({}), after tags sorted:'.format(js['id']))
            else:
                counter += 1
                '''
                print('---------- AnnoJS not similar({}):'.format(js['id']))
                print('---------- (->) {}'.format(json.dumps(js,
                                                             sort_keys=True,
                                                             indent=4)))
                print('---------- (<-) {}'.format(json.dumps(created_js,
                                                             sort_keys=True,
                                                             indent=4)))
                '''
    assert counter == 0



