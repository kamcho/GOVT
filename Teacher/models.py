import uuid as uuid
from django.db import models
import uuid
from Exams.models import  ClassTest
from SubjectList.models import Subject, Topic, Notifications
from Users.models import MyUser, SchoolClass


class TeacherProfile(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE)
    subject = models.ManyToManyField(Subject)

    def subjects_for_grade(self, grade):
        return self.subject.filter(grade=grade)

    def __str__(self):
        return str(self.user)


class StudentList(models.Model):
    user = models.ForeignKey(MyUser, related_name='teacher_user', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_id = models.ForeignKey(SchoolClass,  on_delete=models.CASCADE)

    class Meta:
        unique_together = ('subject', 'class_id')

    def __str__(self):
        return str(self.user)


class ClassTestNotifications(Notifications):
    test = models.ForeignKey(ClassTest, on_delete=models.CASCADE)
    class_id = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.test)
