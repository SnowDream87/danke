import json

from django.core.cache import caches
from django.db.models import Q
from django.db.transaction import atomic
from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.models import District, Agent, HouseType, HouseInfo, HousePhoto, Tag, Role, User, UserRole
from common.utils import to_md5_hex
from common.validators import *


class DistrictSimpleSerializer(serializers.ModelSerializer):
    """地区简单序列化器"""

    class Meta:
        model = District
        fields = ('distid', 'name')


class DistrictDetailSerializer(serializers.ModelSerializer):
    """地区详情序列化器"""
    cities = serializers.SerializerMethodField()

    @staticmethod
    def get_cities(district):
        redis_cli = get_redis_connection()
        data = redis_cli.get(f'zufang:district:{district.distid}:cities')
        if data:
            data = json.loads(data)
        else:
            queryset = District.objects.filter(parent=district).only('name')
            data = DistrictSimpleSerializer(queryset, many=True).data
            redis_cli.set(f'zufang:district:{district.distid}:cities', json.dumps(data), ex=900)
        return data

    class Meta:
        model = District
        exclude = ('parent', )


class AgentSimpleSerializer(serializers.ModelSerializer):
    """经理人简单序列化器"""

    class Meta:
        model = Agent
        fields = ('agentid', 'name', 'tel', 'servstar')


class AgentCreateSerializer(serializers.ModelSerializer):
    """创建经理人序列化器"""

    class Meta:
        model = Agent
        fields = '__all__'


class AgentDetailSerializer(serializers.ModelSerializer):
    """经理人详情序列化器"""

    class Meta:
        model = Agent
        fields = '__all__'


class HouseTypeSerializer(serializers.ModelSerializer):
    """户型序列化器"""

    class Meta:
        model = HouseType
        fields = '__all__'


class HousePhotoSerializer(serializers.ModelSerializer):
    """房屋图片序列化器"""

    class Meta:
        model = HousePhoto
        fields = ('photoid', 'path')


class TagsSerializer(serializers.ModelSerializer):
    """标签序列化器"""

    class Meta:
        model = Tag
        fields = '__all__'


class HouseInfoSimpleSerializer(serializers.ModelSerializer):
    """房源信息简单序列化器"""
    mainphoto = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    @staticmethod
    def get_mainphoto(houseinfo):
        return houseinfo.mainphoto

    @staticmethod
    def get_district(houseinfo):
        return DistrictSimpleSerializer(houseinfo.district_level3).data

    @staticmethod
    def get_type(houseinfo):
        return HouseTypeSerializer(houseinfo.type).data

    @staticmethod
    def get_tags(houseinfo):
        return TagsSerializer(houseinfo.tags, many=True).data

    @staticmethod
    def get_user(houseinfo):
        return UserVerySimpleSerializer(houseinfo.user).data

    class Meta:
        model = HouseInfo
        fields = ('houseid', 'title', 'area', 'floor', 'totalfloor', 'price', 'priceunit',
                  'mainphoto', 'street', 'district', 'type', 'tags', 'user')


class HouseInfoCrateSerializer(serializers.ModelSerializer):
    """创建房源序列化器"""

    class Meta:
        model = HouseInfo
        fields = '__all__'


class HouseInfoDetailSerializer(serializers.ModelSerializer):
    """房源信息详情序列化器"""
    photos = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    agent = serializers.SerializerMethodField()
    mainphoto = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    @staticmethod
    def get_user(houseinfo):
        return UserVerySimpleSerializer(houseinfo.user).data

    @staticmethod
    def get_mainphoto(houseinfo):
        return houseinfo.mainphoto

    @staticmethod
    def get_photos(houseinfo):
        queryset = HousePhoto.objects.filter(house=houseinfo)
        return HousePhotoSerializer(queryset, many=True).data

    @staticmethod
    def get_district(houseinfo):
        return DistrictSimpleSerializer(houseinfo.district_level3).data

    @staticmethod
    def get_type(houseinfo):
        return HouseTypeSerializer(houseinfo.type).data

    @staticmethod
    def get_tags(houseinfo):
        return TagsSerializer(houseinfo.tags, many=True).data

    @staticmethod
    def get_agent(houseinfo):
        return AgentSimpleSerializer(houseinfo.agent).data

    class Meta:
        model = HouseInfo
        exclude = ('district_level2', 'district_level3')


class RoleSimpleSerializer(serializers.ModelSerializer):
    """角色简单序列化器"""

    class Meta:
        model = Role
        fields = ('roleid', )


class UserVerySimpleSerializer(serializers.ModelSerializer):
    """用户简单序列化器"""

    class Meta:
        model = User
        fields = ('realname', 'userid', 'tel')


class UserSimpleSerializer(serializers.ModelSerializer):
    """用户简单序列化器"""

    class Meta:
        model = User
        exclude = ('password', 'roles', 'status')


class UserUpdateSerializer(serializers.ModelSerializer):
    """更新用户序列化器"""

    class Meta:
        model = User
        fields = ('realname', 'username', 'email', 'sex', 'password')


class UserCreateSerializer(serializers.ModelSerializer):
    """创建用户序列化器"""
    username = serializers.RegexField(regex=USERNAME_PATTERN)
    password = serializers.CharField(min_length=6)
    realname = serializers.RegexField(regex=r'[\u4e00-\u9fa5]{2,20}')
    tel = serializers.RegexField(regex=TEL_PATTERN)
    email = serializers.RegexField(regex=EMAIL_PATTERN)
    code = serializers.CharField(write_only=True, min_length=6, max_length=6)

    def validate(self, attrs):
        code_form_user = attrs['code']
        code_redis_user = caches['default'].get(f'{attrs["tel"]}:valid')
        if code_form_user != code_redis_user:
            raise ValidationError('请输入有效的手机验证码', 'invalid')
        user = User.objects.filter(Q(username=attrs['username']) |
                                   Q(tel=attrs['tel']) |
                                   Q(email=attrs['email']))
        if user:
            raise ValidationError(('用户名、手机或邮箱已被注册', 'invalid'))

        return attrs

    def create(self, validated_data):
        del validated_data['code']
        caches['default'].delete(f'{validated_data["tel"]}:valid')
        validated_data['password'] = to_md5_hex(validated_data['password'])
        with atomic():
            user = User.objects.create(**validated_data)
            role = Role.objects.get(roleid=1)
            UserRole.objects.create(user=user, role=role)
        return user

    class Meta:
        model = User
        exclude = ('userid', 'regdate', 'point', 'lastvisit', 'roles')






