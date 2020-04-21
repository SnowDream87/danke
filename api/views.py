import datetime
import random
import os
import time
from common.utils import to_md5_hex

import jwt
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.consts import *
from api.helpers import HouseInfoFilterSet, DefaultResponse, LoginRequiredAuthentication, \
    RbacPermission, authenticate, has_permission
from api.serializers import *
from common.models import District, Agent, HouseType, HouseInfo, User, LoginLog, Role, HouseTag
from common.utils import to_md5_hex, get_ip_address, gen_mobile_code, send_sms_by_luosimao, upload_stream_to_qiniu
from common.validators import check_tel, check_email, check_username
from zufang.settings import SECRET_KEY


@api_view(('POST', ))
def upload_house_photo(request):
    file_obj = request.FILES.get('mainphoto')
    if file_obj and len(file_obj) < MAX_PHOTO_SIZE:
        prefix = to_md5_hex(file_obj.file)
        filename = f'{prefix}{os.path.splitext(file_obj.name)[1]}'
        upload_stream_to_qiniu.delay(file_obj, filename, len(file_obj))
        # photo = HousePhoto()
        # photo.path = f'http://q69nr46pe.bkt.clouddn.com/{filename}'
        # photo.ismain = True
        # photo.save()
        resp = DefaultResponse(*FILE_UPLOAD_SUCCESS, data={
            'url': f'http://q6i8nba3h.bkt.clouddn.com/{filename}'
        })
    else:
        resp = DefaultResponse(*FILE_SIZE_EXCEEDED)
    return resp


@api_view(('GET',))
def get_code_by_sms(request, tel):
    if check_tel(tel):
        if caches['default'].get(f'{tel}:block'):
            res = DefaultResponse(*CODE_TOO_FREQUENCY)
        else:
            code = gen_mobile_code()
            time.sleep(random.random() * 10)
            message = f'您的短信验证码为{code}, 如非本人操作请忽略【铁壳网络】'
            print(message)
            # 成为消息的生产者，并将任务加入队列
            # send_sms_by_luosimao.apply_async((message, tel), countdown=random.random() * 10)
            caches['default'].set(f'{tel}:block', code, timeout=120)
            caches['default'].set(f'{tel}:valid', code, timeout=1800)
            res = DefaultResponse(*MOBILE_CODE_SUCCESS)
    else:
        res = DefaultResponse(*INVALID_TEL_NUM)
    return res


@api_view(('POST', ))
def login(request):
    """登录（获取用户身份令牌）"""
    username = request.data.get('username')
    password = request.data.get('password')
    if (check_tel(username) or check_email(username) or check_username(username)) and len(password) >= 6:
        password = to_md5_hex(password)
        q = Q(username=username, password=password) | \
            Q(tel=username, password=password) | \
            Q(email=username, password=password)
        user = User.objects.filter(q)\
            .only('username', 'realname').first()
        if user:
            if user.status:
                # 用户登录成功通过JWT生成用户身份令牌
                payload = {
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
                    'data': {
                        'userid': user.userid,
                        'realname': user.realname,
                        'roleid': user.roles.get_queryset().first().roleid
                    }
                }
                token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode()
                with atomic():
                    current_time = timezone.now()
                    if not user.lastvisit or \
                            (current_time - user.lastvisit).days >= 1:
                        user.point += 2
                        user.lastvisit = current_time
                        user.save()
                    loginlog = LoginLog()
                    loginlog.user = user
                    loginlog.logdate = current_time
                    loginlog.ipaddr = get_ip_address(request)
                    loginlog.save()
                resp = DefaultResponse(*USER_LOGIN_SUCCESS, data={'token': token})
            else:
                resp = DefaultResponse(*USER_LOGIN_STATUS)
        else:
            resp = DefaultResponse(*USER_LOGIN_FAILED)
    else:
        resp = DefaultResponse(*INVALID_LOGIN_INFO)
    return resp


@api_view(('DELETE',))
def logout(request):
    pass


@cache_page(timeout=365 * 86400)
@api_view(('GET', ))
def get_provinces(request):
    """获取省级行政单位"""
    queryset = District.objects.filter(parent__isnull=True)\
        .only('name')
    serializer = DistrictSimpleSerializer(queryset, many=True)
    return Response({
        'code': 10000,
        'message': '获取省级行政区域成功',
        'results': serializer.data
    })


# @api_view(('GET', ))
# def get_district(request, distid):
#     """获取地区详情"""
#     district = caches['default'].get(f'district:{distid}')
#     if district is None:
#         district = District.objects.filter(distid=distid).first()
#         caches['default'].set(f'district:{distid}', district, timeout=900)
#     serializer = DistrictDetailSerializer(district)
#     return Response(serializer.data)


@api_view(('GET', ))
def get_district(request, distid):
    """获取地区详情"""
    redis_cli = get_redis_connection()
    data = redis_cli.get(f'zufang:district:{distid}')
    if data:
        data = json.loads(data)
    else:
        district = District.objects.filter(distid=distid)\
            .defer('parent').first()
        data = DistrictDetailSerializer(district).data
        redis_cli.set(f'zufang:district:{distid}', json.dumps(data), ex=900)
    return Response(data)


@method_decorator(decorator=cache_page(timeout=3600), name='list')
class TagViewSet(ModelViewSet):
    """标签视图"""
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer


@method_decorator(decorator=cache_page(timeout=3600), name='get')
class HotCityView(ListAPIView):
    """热门城市视图"""
    queryset = District.objects.filter(ishot=True).only('name').all()
    serializer_class = DistrictSimpleSerializer
    pagination_class = None


@method_decorator(decorator=cache_page(timeout=60), name='list')
@method_decorator(decorator=cache_page(timeout=60), name='retrieve')
class AgentViewSet(ModelViewSet):
    """经理人视图
    list:
        获取经理人列表
    retrieve:
        获取经理人详情
    create:
        创建经理人
    update:
        更新经理人信息
    partial_update:
        更新经理人信息
    delete:
        删除经理人
    """
    queryset = Agent.objects.all()

    def get_queryset(self):
        name = self.request.GET.get('name')
        if name:
            self.queryset = self.queryset.filter(name__startswith=name)
        servstar = self.request.GET.get('servstar')
        if servstar:
            self.queryset = self.queryset.filter(servstar__gte=servstar)
        if self.action == 'list':
            self.queryset = self.queryset.only('name', 'tel', 'servstar')
        return self.queryset.order_by('-servstar')

    def get_serializer_class(self):
        if self.action in ('create', 'update'):
            return AgentCreateSerializer
        return AgentDetailSerializer if self.action == 'retrieve' \
            else AgentSimpleSerializer


@method_decorator(decorator=cache_page(timeout=86400), name='list')
@method_decorator(decorator=cache_page(timeout=86400), name='retrieve')
class HouseTypeViewSet(ModelViewSet):
    """户型视图集"""
    queryset = HouseType.objects.all()
    serializer_class = HouseTypeSerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 10000,
            'message': '获取户型成功',
            'results': serializer.data
        })


# @method_decorator(decorator=cache_page(timeout=86400), name='list')
# @method_decorator(decorator=cache_page(timeout=86400), name='retrieve')
# class EstateViewSet(ReadOnlyModelViewSet):
#     """楼盘视图集"""
#     queryset = Estate.objects.all()
#     # 辅助数据筛选
#     filter_backends = (DjangoFilterBackend, OrderingFilter)
#     # filter_fields = ('name', 'hot', 'district') 都是精确条件不够灵活， 所以自定义EstateFilterSet
#     filterset_class = EstateFilterSet
#     ordering = '-hot'
#     ordering_fields = ('district', 'hot', 'name')
#     authentication_classes = (LoginRequiredAuthentication,)
#     permission_classes = (RbacPermission,)
#
#     def get_queryset(self):
#         if self.action == 'list':
#             queryset = self.queryset.only('name')
#         else:
#             queryset = self.queryset\
#                 .defer('district__parent', 'district__ishot', 'district__intro')\
#                 .select_related('district')
#         return queryset
#
#     def get_serializer_class(self):
#         return EstateDetailSerializer if self.action == 'retrieve' else EstateSimpleSerializer


@method_decorator(decorator=cache_page(timeout=60), name='list')
@method_decorator(decorator=cache_page(timeout=60), name='retrieve')
class HouseInfoViewSet(ModelViewSet):
    """房源信息视图集"""
    queryset = HouseInfo.objects.filter(status=True).all()
    serializer_class = HouseInfoDetailSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = HouseInfoFilterSet
    ordering = ('-pubdate',)
    ordering_fields = ('pubdate', 'price')
    # authentication_classes = (LoginRequiredAuthentication,)
    # permission_classes = (RbacPermission,)

    @action(methods=('GET',), detail=True)
    def photos(self, request, pk):
        queryset = HousePhoto.objects.filter(house=self.get_object())
        return Response(HousePhotoSerializer(queryset, many=True).data)

    def get_queryset(self):
        if self.action == 'list':
            return self.queryset\
                .only('houseid', 'title', 'area', 'floor', 'totalfloor', 'price', 'priceunit', 'user',
                      'mainphoto', 'street', 'district_level3__distid', 'district_level3__name', 'type', 'tags')\
                .select_related('district_level3', 'type', 'user')\
                .prefetch_related('tags')
        else:
            return self.queryset\
                .defer('district_level2',
                       'district_level3__parent', 'district_level3__ishot', 'district_level3__intro',
                       'agent__realstar', 'agent__profstar', 'agent__certificated')\
                .select_related('district_level3', 'type', 'agent', 'user')\
                .prefetch_related('tags')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 2000,
            'message': '获取成功',
            'results': [serializer.data]
        })

    def update(self, request, *args, **kwargs):
        data = request.data
        if data:
            houseDate = request.data.get('houseData')
            with atomic():
                house_info = HouseInfo.objects.filter(houseid=kwargs['pk'])
                house_info.update(**houseDate)
                res = Response({
                    'code': 2000,
                    'message': '修改成功',
                })
        else:
            instance = self.get_object()
            instance.status = False
            instance.save()
            res = Response({
                'code': 2000,
                'message': '删除成功',
            })
        return res

    @authenticate    
    @has_permission
    def create(self, request, *args, **kwargs):
        tags = request.data.get('tagData')
        serializer = self.get_serializer(data=request.data.get('houseData'))
        if not serializer.is_valid(raise_exception=True):
            resp = Response({
                'code': 4000,
                'message': '字段错误',
            })
        else:
            with atomic():
                house = serializer.save()
                houseid = house.houseid
                for tag_id in tags.get('tagId'):
                    HouseTag.objects.create(house_id=houseid, tag_id=tag_id)
            resp = Response({
                'code': 2000,
                'message': '添加成功',
            })
        return resp

    def get_serializer_class(self):
        if self.action in ('update', 'create'):
            return HouseInfoCrateSerializer
        return HouseInfoDetailSerializer if self.action == 'retrieve' else HouseInfoSimpleSerializer


class UserViewSet(ModelViewSet):
    """用户模型集视图"""
    queryset = User.objects.filter(status=True).all()
    # authentication_classes = (LoginRequiredAuthentication,)
    # permission_classes = (RbacPermission,)

    @authenticate
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 2000,
            'message': '获取成功',
            'results': [serializer.data]
        })

    @authenticate
    def update(self, request, *args, **kwargs):
        data = request.data

        # 修改角色
        if data.get('role_user'):
            user = self.get_object()
            role = UserRole.objects.filter(user=user).first()
            role.role_id = 2
            role.save()
            return Response({
                'code': 2000,
                'message': '修改成功',
            })
        # 修改用户信息
        if data:
            if data.get('password'):
                password = data.get('password')
                old_password = data.get('oldPassword')
                print(password, old_password)
                user = User.objects.filter(userid=kwargs['pk']).first()
                print(user.password, to_md5_hex(old_password))
                if user.password == to_md5_hex(old_password):
                    user.password = to_md5_hex(password)
                    user.save()
                    res = Response({
                        'code': 2000,
                        'message': '密码修改成功',
                    })
                else:
                    res = Response({
                        'code': 4000,
                        'message': '密码不正确',
                    })
                return res

            else:
                user = User.objects.filter(userid=kwargs['pk'])
                user.update(**data)
                res = Response({
                    'code': 2000,
                    'message': '修改成功',
                })
                
            return res
        # 删除用户
        else:
            instance = self.get_object()
            instance.status = False
            instance.save()
            res = Response({
                'code': 2000,
                'message': '删除成功',
            })
        return res

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'update':
            return UserUpdateSerializer
        return UserSimpleSerializer






