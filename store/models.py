from django.db import models
from django.contrib.auth.models import Group

class Store(models.Model):

    name = models.CharField(max_length=50)
    status = models.IntegerField(default=1)

    def __str__(self):
        return self.name


class PagePermission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='page_permissions')
    page_slug = models.CharField(max_length=100)

    class Meta:
        unique_together = ('group', 'page_slug')

    def __str__(self):
        return f"{self.group.name} → {self.page_slug}"