"""__ author__= 小孩子 """
from datetime import timedelta

from django.db import DatabaseError
from django.utils import timezone

from common.models import Record


def remove_expired_records():

	check_time = timezone.now() - timedelta(days=90)
	try:
		Record.objects.filter(recorddate__lte=check_time).delete()
		return True
	except DatabaseError:
		return False


