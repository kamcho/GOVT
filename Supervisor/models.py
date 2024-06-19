
from django.db import models
from Guardian.views import MyKidsView
from SubjectList.models import Subject, Topic, Subtopic
from Term.models import Terms
from Users.models import MyUser, SchoolClass


class FeeMigrations(models.Model):
    term = models.OneToOneField(Terms, on_delete=models.CASCADE) # type: ignore
    date = models.DateField(auto_now=True)
    increment = models.PositiveIntegerField()
    current_balance = models.PositiveIntegerField()
    new_balances = models.PositiveIntegerField()

    def __str__(self):
        return str(self.date)

class Promotion(models.Model):
    year = models.PositiveIntegerField()
    classes = models.ManyToManyField(SchoolClass)

class Updates(models.Model):
    title = models.CharField(max_length=300)
    description = models.TextField(max_length=500)
    date = models.DateField(auto_now=True)
    file = models.FileField(upload_to='Updates/', null=True)

    def __str__(self):
        return str(self.title)
    
class FileModel(models.Model):
    file = models.FileField(upload_to='gallery/')  # Choose your upload_to path


class ExtraCurricular(models.Model):
    user = models.ForeignKey(MyUser, related_name='teacher', on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    description = models.TextField(max_length=500)
    date = models.DateField(auto_now=True)
    files = models.ManyToManyField(FileModel)  # Assuming you have a model to store files
    students = models.ManyToManyField(MyUser)

    def __str__(self):
        return str(self.title)

