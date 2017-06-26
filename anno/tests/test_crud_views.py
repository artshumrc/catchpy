import json
import pytest

from django.urls import reverse
from django.test import Client

from anno.anno_defaults import ANNO, TEXT
from anno.anno_defaults import ANNOTATORJS_FORMAT
from anno.anno_defaults import CATCH_RESPONSE_FORMAT_HTTPHEADER
from anno.crud import CRUD
from anno.models import Anno
from anno.views import crud_api

from consumer.models import Consumer

from .conftest import make_encoded_token
from .conftest import make_jwt_payload
from .conftest import make_json_request
from .conftest import make_request
from .conftest import make_wa_object


#@pytest.mark.django_db
def test_index():

    client = Client()
    url = reverse('index')
    print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&({})'.format(url))
    response = client.get(url)
    print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&({})'.format(response.content))

    from django.core.urlresolvers import resolve
    func = resolve(url).func
    func_name = '{}.{}'.format(func.__module__, func.__name__)
    print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&({})'.format(func_name))

    assert response.status_code == 200


@pytest.mark.django_db
def test_method_not_allowed(wa_audio):
    request = make_request(method='patch')
    response = crud_api(request, '1234')
    assert response.status_code == 405


@pytest.mark.usefixtures('wa_audio')
@pytest.mark.django_db
def test_read_ok(wa_audio):
    catcha = wa_audio
    x = CRUD.create_anno(catcha)

    request = make_request(method='get', anno_id=x.anno_id)
    response = crud_api(request, x.anno_id)
    assert response.status_code == 200
    assert response.content is not None


@pytest.mark.usefixtures('wa_audio')
@pytest.mark.django_db
def test_head_ok(wa_audio):
    catcha = wa_audio
    x = CRUD.create_anno(catcha)
    c = Consumer._default_manager.create()
    payload = make_jwt_payload(apikey=c.consumer)
    token = make_encoded_token(c.secret_key, payload)

    client = Client()  # check if middleware works
    response = client.head(
        reverse('crud_api', kwargs={'anno_id': x.anno_id}),
        HTTP_AUTHORIZATION='token ' + token)

    assert response.status_code == 200
    assert len(response.content) == 0


@pytest.mark.django_db
def test_read_not_found():
    c = Consumer._default_manager.create()
    payload = make_jwt_payload(apikey=c.consumer)
    token = make_encoded_token(c.secret_key, payload)

    client = Client()  # check if middleware works
    url = reverse('crud_api', kwargs={'anno_id': '1234567890-fake-fake'})
    print('*********** {}'.format(url))
    response = client.get(
        url,
        HTTP_X_ANNOTATOR_AUTH_TOKEN=token)
    print('*********** {}'.format(response.content))
    assert response.status_code == 404


@pytest.mark.usefixtures('wa_audio')
@pytest.mark.django_db
def test_delete_ok(wa_audio):
    catcha = wa_audio
    x = CRUD.create_anno(catcha)
    payload = make_jwt_payload(user=x.creator_id)

    request = make_request(
        method='delete', jwt_payload=payload, anno_id=x.anno_id)

    response = crud_api(request, x.anno_id)
    assert response.status_code == 200
    assert response.content is not None

    request = make_request(  # try to read deleted anno
        method='get', jwt_payload=payload, anno_id=x.anno_id)
    response = crud_api(request, x.anno_id)
    assert response.status_code == 404


@pytest.mark.usefixtures('wa_audio')
@pytest.mark.django_db
def test_delete_with_override(wa_audio):
    catcha = wa_audio
    x = CRUD.create_anno(catcha)
    # requesting user is not the creator, but has override to delete
    payload = make_jwt_payload(user='fake_user', override=['CAN_DELETE'])

    request = make_request(method='delete', anno_id=x.anno_id)
    request.catchjwt = payload

    response = crud_api(request, x.anno_id)
    assert response.status_code == 200
    assert response.content is not None

    request = make_request(method='get', anno_id=x.anno_id)
    request.catchjwt = payload
    response = crud_api(request, x.anno_id)
    assert response.status_code == 404


@pytest.mark.usefixtures('wa_text')
@pytest.mark.django_db
def test_update_no_body_in_request(wa_text):
    catcha = wa_text
    x = CRUD.create_anno(catcha)
    payload = make_jwt_payload(user=catcha['creator']['id'])

    request = make_request(method='put', anno_id=x.anno_id)
    request.catchjwt = payload

    response = crud_api(request, x.anno_id)
    assert response.status_code == 400
    resp = json.loads(response.content)
    assert len(resp['payload']) > 0
    assert 'missing json' in ','.join(resp['payload'])


@pytest.mark.usefixtures('wa_video')
@pytest.mark.django_db
def test_update_invalid_input(wa_video):
    catcha = wa_video
    x = CRUD.create_anno(catcha)
    payload = make_jwt_payload(user=x.creator_id)

    data = dict(catcha)
    data['body'] = {}
    request = make_json_request(
        method='put', anno_id=x.anno_id, data=json.dumps(data))
    request.catchjwt = payload

    response = crud_api(request, x.anno_id)
    assert response.status_code == 400
    resp = json.loads(response.content)
    assert len(resp['payload']) > 0


@pytest.mark.usefixtures('wa_video')
@pytest.mark.django_db
def test_update_denied_can_admin(wa_video):
    catch = wa_video
    payload = make_jwt_payload()
    # requesting user is allowed to update but not admin
    catch['permissions']['can_update'].append(payload['userId'])
    x = CRUD.create_anno(catch)

    data = dict(catch)
    # trying to update permissions
    data['permissions']['can_delete'].append(payload['userId'])
    request = make_json_request(
        method='put', anno_id=x.anno_id, data=json.dumps(data))
    request.catchjwt = payload

    response = crud_api(request, x.anno_id)
    resp = json.loads(response.content)
    assert response.status_code == 403
    assert len(resp['payload']) > 0
    assert 'not allowed to admin' in ','.join(resp['payload'])


@pytest.mark.usefixtures('wa_text')
@pytest.mark.django_db
def test_update_ok(wa_text):
    catch = wa_text
    payload = make_jwt_payload()
    # requesting user is allowed to update but not admin
    catch['permissions']['can_update'].append(payload['userId'])
    x = CRUD.create_anno(catch)

    original_tags = x.anno_tags.count()
    original_targets = x.total_targets

    data = catch.copy()
    data['body']['items'].append({'type': 'TextualBody',
                                  'purpose': 'tagging',
                                  'value': 'winsome'})
    assert data['id'] is not None
    assert data['creator']['id'] is not None
    assert 'contextId' in data['platform']

    request = make_json_request(
        method='put', anno_id=x.anno_id, data=json.dumps(data))
    request.catchjwt = payload

    response = crud_api(request, x.anno_id)
    resp = json.loads(response.content)
    assert response.status_code == 200
    assert 'Location' in response
    assert response['Location'] is not None
    assert x.anno_id in response['Location']

    assert len(resp['body']['items']) == original_tags + 2
    assert len(resp['target']['items']) == original_targets


@pytest.mark.usefixtures('wa_image')
@pytest.mark.django_db
def test_create_on_behalf_of_others(wa_image):
    to_be_created_id = '1234-5678-abcd-0987'
    catch = wa_image
    payload = make_jwt_payload()

    request = make_json_request(
        method='post', anno_id=to_be_created_id, data=json.dumps(catch))
    request.catchjwt = payload

    assert catch['id'] != to_be_created_id
    assert catch['creator']['id'] != payload['userId']

    response = crud_api(request, to_be_created_id)
    resp = json.loads(response.content)
    assert response.status_code == 409
    assert 'conflict in input creator_id' in ','.join(resp['payload'])


@pytest.mark.usefixtures('wa_image')
@pytest.mark.django_db
def test_create_ok(wa_image):
    to_be_created_id = '1234-5678-abcd-0987'
    catch = wa_image
    payload = make_jwt_payload(user=catch['creator']['id'])

    request = make_json_request(
        method='post', anno_id=to_be_created_id, data=json.dumps(catch))
    request.catchjwt = payload

    response = crud_api(request, to_be_created_id)
    resp = json.loads(response.content)

    assert response.status_code == 200
    assert 'Location' in response
    assert response['Location'] is not None
    assert to_be_created_id in response['Location']
    assert resp['id'] == to_be_created_id
    assert resp['creator']['id'] == payload['userId']

    x = Anno._default_manager.get(pk=to_be_created_id)
    assert x.creator_id == payload['userId']


@pytest.mark.usefixtures('wa_audio')
@pytest.mark.django_db
def test_create_duplicate(wa_audio):
    catch = wa_audio
    x = CRUD.create_anno(catch)
    payload = make_jwt_payload(user=catch['creator']['id'])

    request = make_json_request(
        method='post', anno_id=x.anno_id, data=json.dumps(catch))
    request.catchjwt = payload

    response = crud_api(request, x.anno_id)
    assert response.status_code == 409
    resp = json.loads(response.content)
    assert 'failed to create' in resp['payload'][0]


@pytest.mark.usefixtures('js_text')
@pytest.mark.django_db
def test_create_annojs(js_text):
    js = js_text
    to_be_created_id = '1234-5678-0987-6543'
    payload = make_jwt_payload(user=js['user']['id'])

    request = make_json_request(
        method='post', anno_id=to_be_created_id, data=json.dumps(js))
    request.META[CATCH_RESPONSE_FORMAT_HTTPHEADER] = ANNOTATORJS_FORMAT
    request.catchjwt = payload

    assert js['id'] != to_be_created_id

    response = crud_api(request, to_be_created_id)
    resp = json.loads(response.content)

    assert response.status_code == 200
    assert resp['id'] == to_be_created_id
    assert resp['user']['id'] == payload['userId']
    assert len(resp['tags']) == len(js['tags'])
    assert resp['contextId'] == js['contextId']

    x = Anno._default_manager.get(pk=to_be_created_id)
    assert x.creator_id == payload['userId']

@pytest.mark.usefixtures('wa_audio')
@pytest.mark.django_db
def test_create_reply(wa_audio):
    to_be_created_id = '1234-5678-abcd-efgh'
    x = CRUD.create_anno(wa_audio)
    catch = make_wa_object(age_in_hours=30, media=ANNO, reply_to=x.anno_id)
    payload = make_jwt_payload(user=catch['creator']['id'])

    request = make_json_request(
        method='post', anno_id=to_be_created_id, data=json.dumps(catch))
    request.catchjwt = payload

    response = crud_api(request, to_be_created_id)
    resp = json.loads(response.content)
    assert response.status_code == 200
    assert 'Location' in response
    assert response['Location'] is not None
    assert to_be_created_id in response['Location']
    assert resp['id'] == to_be_created_id
    assert resp['creator']['id'] == payload['userId']

    x = Anno._default_manager.get(pk=to_be_created_id)
    assert x.creator_id == payload['userId']


@pytest.mark.django_db
def test_create_reply_to_itself():
    to_be_created_id = '1234-5678-abcd-efgh'
    catch = make_wa_object(age_in_hours=30, media=ANNO,
                           reply_to=to_be_created_id)
    payload = make_jwt_payload(user=catch['creator']['id'])

    request = make_json_request(
        method='post', anno_id=to_be_created_id, data=json.dumps(catch))
    request.catchjwt = payload

    response = crud_api(request, to_be_created_id)
    resp = json.loads(response.content)
    assert response.status_code == 409
    assert 'cannot be a reply to itself' in resp['payload'][0]


@pytest.mark.usefixtures('wa_audio')
@pytest.mark.django_db
def test_create_reply_missing_target(wa_audio):
    to_be_created_id = '1234-5678-abcd-efgh'
    x = CRUD.create_anno(wa_audio)
    catch = make_wa_object(age_in_hours=30, media=ANNO, reply_to=x.anno_id)
    payload = make_jwt_payload(user=catch['creator']['id'])

    # remove target item with media type 'ANNO'
    catch['target']['items'][0]['type'] = TEXT

    request = make_json_request(
        method='post', anno_id=to_be_created_id, data=json.dumps(catch))
    request.catchjwt = payload

    response = crud_api(request, to_be_created_id)
    resp = json.loads(response.content)
    assert response.status_code == 409
    assert 'missing parent reference' in resp['payload'][0]

    with pytest.raises(Anno.DoesNotExist):
        x = Anno._default_manager.get(pk=to_be_created_id)


@pytest.mark.usefixtures('wa_audio')
@pytest.mark.django_db
def test_create_reply_missing_target(wa_audio):
    to_be_created_id = '1234-5678-abcd-efgh'
    x = CRUD.create_anno(wa_audio)
    catch = make_wa_object(age_in_hours=30, media=ANNO, reply_to=x.anno_id)
    payload = make_jwt_payload(user=catch['creator']['id'])

    # replace target source
    catch['target']['items'][0]['source'] = 'fake_parent_reference'

    request = make_json_request(
        method='post', anno_id=to_be_created_id, data=json.dumps(catch))
    request.catchjwt = payload

    response = crud_api(request, to_be_created_id)
    resp = json.loads(response.content)
    assert response.status_code == 409
    assert 'conflicting target_source_id' in resp['payload'][0]

    with pytest.raises(Anno.DoesNotExist):
        x = Anno._default_manager.get(pk=to_be_created_id)

