import datetime
from functools import lru_cache, wraps

import jwt
from django.db.models import Q, Prefetch
from jwt import DecodeError, InvalidTokenError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import PageNumberPagination, CursorPagination
from django_filters import filterset
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from common.models import HouseInfo, User, Role
from zufang.settings import SECRET_KEY


def authenticate(func):

    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        token = request.META.get('HTTP_TOKEN')
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY)
                user = User()
                user.userid = payload['data']['userid']
                return func(self, request, user, *args, **kwargs)

            except InvalidTokenError:
                return Response({
                    'code': 4001,
                    'message': '无效的令牌或令牌已过期',
                })
        return Response({
            'code': 4002,
            'message': '请提供有效的身份标识',
        })

    return wrapper


def has_permission(func):

    @wraps(func)
    def wrapper(self, request, user, *args, **kwargs):
        privs = get_privs_by_user(user.userid)
        for priv in privs:
            if request.method == priv.method and request.path == priv.url:
                return func(self, request, *args, **kwargs)
        return Response({
            'code': 4003,
            'message': '你没有该权限',
        })

    return wrapper


class LoginRequiredAuthentication(BaseAuthentication):
    """登录认证"""

    # 如果用户身份验证成功需要返回一个二元组(user, token)
    def authenticate(self, request):
        token = request.META.get('HTTP_TOKEN')
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY)
                user = User()
                user.userid = payload['data']['userid']
                user.is_authenticated = True
                return user, token
            except InvalidTokenError:
                raise AuthenticationFailed('无效的令牌或令牌已过期')
        raise AuthenticationFailed('请提供有效的身份标识')


class RbacPermission(BasePermission):
    """RBAC授权"""

    def has_permission(self, request, view):
        privs = get_privs_by_user(request.user.userid)
        for priv in privs:
            if request.method == priv.method and request.path == priv.url:
                return True
        return False


@lru_cache(maxsize=256)
def get_privs_by_user(userid):

    user = User.objects.filter(userid=userid)\
        .prefetch_related(
            Prefetch(
                'roles', queryset=Role.objects.all().prefetch_related('privs'))
    ).first()
    return [priv for role in user.roles.all()
            for priv in role.privs.all()]


class DefaultResponse(Response):
    """定义返回JSON数据的响应类"""

    def __init__(self, code=100000, message='操作成功',
                 data=None, status=None, template_name=None,
                 headers=None, exception=False, content_type=None):
        _data = {'code': code, 'message': message}
        if data:
            _data.update(data)
        super().__init__(_data, status, template_name,
                         headers, exception, content_type)


class CustomPagePagination(PageNumberPagination):
    """自定义页码分页类"""
    page_size_query_param = 'size'
    max_page_size = 50


class AgentCursorPagination(CursorPagination):
    """经理人游标分页类"""
    page_size_query_param = 'size'
    max_page_size = 50
    ordering = '-agentid'


# class EstateFilterSet(filterset.FilterSet):
#     """自定义楼盘筛选器"""
#     name = filterset.CharFilter(lookup_expr='startswith')
#     minhot = filterset.NumberFilter(field_name='hot', lookup_expr='gte')
#     maxhot = filterset.NumberFilter(field_name='hot', lookup_expr='lte')
#     dist = filterset.NumberFilter(field_name='district')
#
#     class Meta:
#         model = Estate
#         fields = ('name', 'minhot', 'maxhot', 'dist')


class HouseInfoFilterSet(filterset.FilterSet):
    """自定义房源筛选器"""
    title = filterset.CharFilter(lookup_expr='contains')
    minprice = filterset.NumberFilter(field_name='price', lookup_expr='gte')
    maxprice = filterset.NumberFilter(field_name='price', lookup_expr='lte')
    minarea = filterset.NumberFilter(field_name='area', lookup_expr='gte')
    maxarea = filterset.NumberFilter(field_name='area', lookup_expr='lte')
    housetype = filterset.NumberFilter(field_name='type')
    user = filterset.NumberFilter(field_name='user')
    district = filterset.NumberFilter(method='filter_by_district')

    @staticmethod
    def filter_by_district(queryset, name, value):
        return queryset.filter(Q(district_level2=value) |
                               Q(district_level3=value))

    class Meta:
        model = HouseInfo
        fields = ('title', 'minprice', 'maxprice', 'minarea', 'maxarea', 'district')


