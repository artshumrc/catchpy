from datetime import datetime
import dateutil
import json
import logging

from django.db.models import Q
from django.conf import settings
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from http import HTTPStatus

from .json_models import AnnoJS
from .json_models import Catcha
from .crud import CRUD
from .decorators import require_catchjwt
from .errors import AnnoError
from .errors import AnnotatorJSError
from .errors import InconsistentAnnotationError
from .errors import InvalidAnnotationCreatorError
from .errors import DuplicateAnnotationIdError
from .errors import MethodNotAllowedError
from .errors import MissingAnnotationError
from .errors import MissingAnnotationInputError
from .errors import NoPermissionForOperationError
from .errors import UnknownResponseFormatError
from .search import query_username
from .search import query_userid
from .search import query_tags
from .search import query_target_medias
from .search import query_target_sources
from .models import Anno
from .utils import generate_uid

from .anno_defaults import ANNO
from .anno_defaults import ANNOTATORJS_FORMAT
from .anno_defaults import CATCH_ADMIN_GROUP_ID
from .anno_defaults import CATCH_ANNO_FORMAT
from .anno_defaults import CATCH_CURRENT_SCHEMA_VERSION
from .anno_defaults import CATCH_JSONLD_CONTEXT_IRI
from .anno_defaults import CATCH_RESPONSE_LIMIT
from .anno_defaults import CATCH_LOG_SEARCH_TIME


logger = logging.getLogger(__name__)



@require_http_methods(['GET', 'HEAD'])
@csrf_exempt
@require_catchjwt
def stats_api(request, context_id):

    # info log
    logger.info('[{0} stats for context_id({2})'.format(
        request.catchjwt['consumerKey'],
        context_id,
    ))

    # list of collection_ids in context
    collections = get_collection_list(context_id)
    qs_per_context = Anno._default_manager.filter(
        Anno.custom_manager.search_expression({'context_id': context_id}))

    stats = {}
    collection_stats = []
    annos_per_context = 0
    for collection_id in collections:
        annos_per_collection = 0
        # list of target_ids in collection
        targets = get_target_list(context_id, collection_id)

        target_stats = []
        for target_id in targets:
            qs_per_target = qs_per_context.filter(
                Anno.default_manager.search_expression(
                    {'collection_id': collection_id,
                     'source_id': target_id}
                )
            )
            annos_per_target = len(qs_per_target)
            target_stats.append({
                'context_id': context_id,
                'collection_id': collection_id,
                'target_source_id': target_id,
                'total_annos': annos_per_target,
            })
            annos_per_collection += len(qs_per_target)

        collection_stats.append({
            'context_id': context_id,
            'collection_id': collection_id,
            'total_annos': annos_per_collection,
            'total_targets': len(target_stats),
            'target_stats': target_stats,
        })
        annos_per_context += annos_per_collection

    stats = {
        'context_id': context_id,
        'total_annos': annos_per_context,
        'total_collections': len(collection_stats),
        'collection_stats': collection_stats,
    }

    status = HTTPStatus.OK
    response = JsonResponse(status=status, data=stats)
    return response




def get_collection_list(context_id):
    '''returns list of distinct collection ids for context.'''

    collection_list = Anno._default_manager.filter(
        raw__platform__context_id=context_id
    ).values_list(
        'raw__platform__collection_id'
    ).distinct()
    logger.info('--------------- collection_list({}): ({})'.format(
        len(collection_list),
        collection_list,
    ))
    return collection_list


def get_target_list(context_id, collection_id):
    '''returns list of distinct target ids for context, collection.'''

    target_list = Anno._default_manager.filter(
        raw__platform__context_id=context_id,
        raw__platform__collection_id=collection_id
    ).values_list(
        'raw__platform__target_source_id'
    ).distinct()
    logger.info('--------------- target_list({}): ({})'.format(
        len(target_list),
        target_list,
    ))
    return target_list






