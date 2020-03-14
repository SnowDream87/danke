"""
租房网项目公共模型
"""
from django.db import models


# class BaseModel(models.Model):
#     """自定义模型的基类（保存公共字段和方法）"""
#     create_time = models.DateTimeField(auto_now_add=True)
#     update_time = models.DateTimeField(auto_now=True)
#     deleted = models.BooleanField(default=False)
#
#     class Meta:
#         abstract = True


class User(models.Model):
    """用户"""
    # 用户ID
    userid = models.AutoField(primary_key=True)
    # 用户名
    username = models.CharField(unique=True, max_length=20)
    # 用户密码（数据库中保存MD5摘要，登录时比较密码的签名）
    password = models.CharField(max_length=32)
    # 用户真实姓名
    realname = models.CharField(max_length=20)
    # 用户性别
    sex = models.BooleanField(default=True)
    # 用户电话
    tel = models.CharField(unique=True, max_length=20)
    # 用户邮箱
    email = models.CharField(unique=True, max_length=255, default='')
    # 用户注册日期
    regdate = models.DateTimeField(auto_now_add=True)
    # 用户积分（每天登录可以获得积分）
    point = models.IntegerField(default=0)
    # 用户最后登录日期时间
    lastvisit = models.DateTimeField(blank=True, null=True)
    # 用户角色
    roles = models.ManyToManyField(to='Role', through='UserRole')

    class Meta:
        managed = False
        db_table = 'tb_user'


class District(models.Model):
    """地区"""
    # 地区ID
    distid = models.IntegerField(primary_key=True)
    # 父级行政区域（省级行政区域的父级为None）
    parent = models.ForeignKey(to='self', on_delete=models.DO_NOTHING, db_column='pid', null=True)
    # 地区名称
    name = models.CharField(max_length=255)
    # 该地区是不是热门城市
    ishot = models.BooleanField(default=False)
    # 地区介绍
    intro = models.CharField(max_length=255, default='')

    class Meta:
        managed = False
        db_table = 'tb_district'


class Agent(models.Model):
    """经理人"""
    # 经理人ID
    agentid = models.AutoField(primary_key=True)
    # 经理人姓名
    name = models.CharField(max_length=255)
    # 经理人电话
    tel = models.CharField(max_length=20)
    # 经理人服务星级
    servstar = models.IntegerField()
    # 经理人提供的房源真实度
    realstar = models.IntegerField()
    # 经理人业务水平
    profstar = models.IntegerField()
    # 经理人是否持有专业认证
    certificated = models.BooleanField(default=False)
    # 经理人负责的楼盘
    estates = models.ManyToManyField(to='Estate', through='AgentEstate')

    class Meta:
        managed = False
        db_table = 'tb_agent'


class Estate(models.Model):
    """楼盘"""
    # 楼盘ID
    estateid = models.AutoField(primary_key=True)
    # 所属行政区域
    district = models.ForeignKey(to=District, on_delete=models.DO_NOTHING, db_column='distid')
    # 楼盘名称
    name = models.CharField(max_length=255)
    # 楼盘热度
    hot = models.IntegerField(default=0)
    # 楼盘介绍
    intro = models.CharField(max_length=511, default='')

    class Meta:
        managed = False
        db_table = 'tb_estate'


class AgentEstate(models.Model):
    """经理人楼盘中间实体"""
    agent_estate_id = models.AutoField(primary_key=True)
    # 经理人
    agent = models.ForeignKey(to=Agent, on_delete=models.DO_NOTHING, db_column='agentid')
    # 楼盘
    estate = models.ForeignKey(to=Estate, on_delete=models.DO_NOTHING, db_column='estateid')

    class Meta:
        managed = False
        db_table = 'tb_agent_estate'
        unique_together = (('agent', 'estate'), )


class HouseType(models.Model):
    """户型"""
    # 户型ID
    typeid = models.IntegerField(primary_key=True)
    # 户型名称
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'tb_house_type'


class HouseInfo(models.Model):
    """房源信息"""
    # 房源ID
    houseid = models.AutoField(primary_key=True)
    # 房源标题
    title = models.CharField(max_length=50)
    # 房源面积
    area = models.IntegerField()
    # 房源楼层
    floor = models.IntegerField()
    # 房源总楼层
    totalfloor = models.IntegerField()
    # 房源朝向
    direction = models.CharField(max_length=10)
    # 房源价格
    price = models.IntegerField()
    # 房源价格单位
    priceunit = models.CharField(max_length=10)
    # 房源详情
    detail = models.CharField(max_length=511, default='')
    # 房源图片（主图）
    mainphoto = models.CharField(max_length=255)
    # 房源发布日期
    pubdate = models.DateField(auto_now_add=True)
    # 房源所在街道
    street = models.CharField(max_length=255)
    # 是否有地铁
    hassubway = models.BooleanField(default=False)
    # 是否支持合租
    isshared = models.BooleanField(default=False)
    # 是否有中介费
    hasagentfees = models.BooleanField(default=False)
    # 房源户型
    type = models.ForeignKey(to=HouseType, on_delete=models.DO_NOTHING, db_column='typeid')
    # 房源发布者
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, db_column='userid')
    # 给ForeignKey加上related_name='+'可以避免多对一关系从一的一方向多的一方发起查询
    # 房源所属二级行政区域
    district_level2 = models.ForeignKey(to=District, on_delete=models.DO_NOTHING, related_name='+', db_column='distid2')
    # 房源所属三级行政区域
    district_level3 = models.ForeignKey(to=District, on_delete=models.DO_NOTHING, related_name='+', db_column='distid3')
    # 房源所属楼盘
    estate = models.ForeignKey(to=Estate, on_delete=models.DO_NOTHING, db_column='estateid', null=True)
    # 负责该房源的经理人
    agent = models.ForeignKey(to=Agent, on_delete=models.DO_NOTHING, db_column='agentid', null=True)
    # 房源标签
    tags = models.ManyToManyField(to='Tag', through='HouseTag')

    class Meta:
        managed = False
        db_table = 'tb_house_info'


class HousePhoto(models.Model):
    """房源的图片"""
    # 图片ID
    photoid = models.AutoField(primary_key=True)
    # 图片对应的房源
    house = models.ForeignKey(to=HouseInfo, on_delete=models.DO_NOTHING, db_column='houseid')
    # 图片资源路径
    path = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'tb_house_photo'


class Tag(models.Model):
    """标签"""
    # 标签ID
    tagid = models.AutoField(primary_key=True)
    # 标签内容
    content = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'tb_tag'


class HouseTag(models.Model):
    """房源标签中间实体"""
    house_tag_id = models.AutoField(primary_key=True)
    # 房源
    house = models.ForeignKey(to=HouseInfo, on_delete=models.DO_NOTHING, db_column='houseid')
    # 标签
    tag = models.ForeignKey(to=Tag, on_delete=models.DO_NOTHING, db_column='tagid')

    class Meta:
        managed = False
        db_table = 'tb_house_tag'
        unique_together = (('house', 'tag'), )


class Record(models.Model):
    """浏览记录"""
    # 浏览记录ID
    recordid = models.BigAutoField(primary_key=True)
    # 浏览的用户
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, db_column='userid')
    # 浏览的房源
    house = models.ForeignKey(to=HouseInfo, on_delete=models.DO_NOTHING, db_column='houseid')
    # 浏览日路日期
    recorddate = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'tb_record'
        unique_together = (('user', 'house'), )


class LoginLog(models.Model):
    """登录日志"""
    # 日志ID
    logid = models.BigAutoField(primary_key=True)
    # 登录的用户
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, db_column='userid')
    # 登录的IP地址
    ipaddr = models.CharField(max_length=255)
    # 登录的日期
    logdate = models.DateTimeField(auto_now_add=True)
    # 登录的设备编码
    devcode = models.CharField(max_length=255, default='')

    class Meta:
        managed = False
        db_table = 'tb_login_log'


class Role(models.Model):
    """角色"""
    # 角色ID
    roleid = models.AutoField(primary_key=True)
    # 角色名称
    rolename = models.CharField(max_length=255)
    # 角色对应的权限
    privs = models.ManyToManyField(to='Privilege', through='RolePrivilege')

    class Meta:
        managed = False
        db_table = 'tb_role'


class Privilege(models.Model):
    """权限"""
    # 权限ID
    privid = models.AutoField(primary_key=True)
    # 权限对应的方法
    method = models.CharField(max_length=15)
    # 权限对应的URL
    url = models.CharField(max_length=1024)
    # 权限的描述
    detail = models.CharField(max_length=255, default='')

    class Meta:
        managed = False
        db_table = 'tb_privilege'


class UserRole(models.Model):
    """用户角色中间实体"""
    user_role_id = models.AutoField(primary_key=True)
    # 用户
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, db_column='userid')
    # 角色
    role = models.ForeignKey(to=Role, on_delete=models.DO_NOTHING, db_column='roleid')

    class Meta:
        managed = False
        db_table = 'tb_user_role'
        unique_together = (('user', 'role'), )


class RolePrivilege(models.Model):
    """角色权限中间实体"""
    role_priv_id = models.AutoField(primary_key=True)
    # 角色
    role = models.ForeignKey(to=Role, on_delete=models.DO_NOTHING, db_column='roleid')
    # 权限
    priv = models.ForeignKey(to=Privilege, on_delete=models.DO_NOTHING, db_column='privid')

    class Meta:
        managed = False
        db_table = 'tb_role_privilege'
        unique_together = (('role', 'priv'), )
