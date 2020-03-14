from django.http import HttpResponse
from django.shortcuts import render

from common.captcha import Captcha
from common.utils import gen_captcha_text


def index(request):
    return render(request, 'index.html')


def login(request):
    return render(request, 'login.html')


def register(request):
    return render(request, 'register.html')


def publish(request):
    return render(request, 'publish.html')


def user_info(request):
    return render(request, 'userInfo.html')


def house_info(request, houseid):
    return render(request, 'houseinfo.html', {houseid:houseid})


def get_captcha(request):
    instance = Captcha.instance()
    text = gen_captcha_text()
    data = instance.generate(text)
    return HttpResponse(data, content_type='image/png')
