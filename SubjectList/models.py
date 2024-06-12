from click import prompt
from django.db import models
import uuid
from Users.models import MyUser


class Course(models.Model):
    name = models.CharField(max_length=100)
    discipline = models.CharField(max_length=20)
    abbreviation = models.CharField(max_length=10, default='Math')

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=1)
    grade = models.CharField(max_length=2)
    topics = models.PositiveIntegerField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    abbreviation = models.CharField(max_length=10, default='DEF')

    def get_grade(self, score):
        # Define the grade ranges for each subject
        if self.name == 'Mathematics':
            if score >= 70:
                return 'A', 12
            elif score >= 65 and score <= 69:
                return 'A-', 11
            elif score >= 60 and score <= 64:
                return 'B+', 10
            elif score >= 55 and score <= 59:
                return 'B', 9
            elif score >= 49 and score <= 54:
                return 'B-', 8
            elif score >= 43 and score <= 48:
                return 'C+', 7
            elif score >= 37 and score <= 42:
                return 'C', 6
            elif score >= 31 and score <= 36:
                return 'C-', 5
            elif score >= 25 and score <= 30:
                return 'D+', 4
            elif score >= 19 and score <= 24:
                return 'D', 3
            elif score >= 12 and score <= 18:
                return 'D-', 2
            elif score >= 0 and score <= 11:
                return 'E', 1
            else:
                return 'U',0
            
        
        # if self.name in ['English', 'Biology', 'History', 'Business']:
        else:
            if score >= 80:
                return 'A', 12
            elif score >= 75 and score <= 79:
                return 'A-', 11
            elif score >= 70 and score <= 74:
                return 'B+', 10
            elif score >= 65 and score <= 69:
                return 'B', 9
            elif score >= 60 and score <= 64:
                return 'B-', 8
            elif score >= 55 and score <= 59:
                return 'C+', 7
            elif score >= 50 and score <= 54:
                return 'C', 6
            elif score >= 45 and score <= 49:
                return 'C-', 5
            elif score >= 40 and score <= 44:
                return 'D+', 4
            elif score >= 35 and score <= 39:
                return 'D', 3
            elif score >= 30 and score <= 34:
                return 'D-', 2
            elif score >= 0 and score <= 29:
                return 'E', 1
            else:
                return 'U', 0


    def __str__(self):
        return str(self.name)


class MySubjects(models.Model):
    name = models.ManyToManyField(Course, blank=True, related_name='my_subjects')
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)

    def selected(self):
        if self.name.exists():
            return 'True'
        else:
            return 'False'


class Topic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.IntegerField()
    subject = models.ForeignKey(Subject, related_name='subject_id', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    topics_count = models.CharField(max_length=5)
    test_size = models.PositiveIntegerField()
    time = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Subtopic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='topic')
    name = models.CharField(max_length=100)
    file1 = models.FileField(upload_to='studyFiles', default='file.pdf')
    file2 = models.FileField(upload_to='studyFiles', default='start.mp4')
    order = models.CharField(max_length=5)

    def __str__(self):
        return self.name


class Progress(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    subtopic = models.ManyToManyField(Subtopic, related_name='progress_subtopic')
    topic = models.ManyToManyField(Topic, related_name='progress')

    def __str__(self):
        return str(self.user)


class Notifications(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=100)
    message = models.TextField(max_length=500)
    about = models.CharField(max_length=100)
    is_read = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class TopicExamNotifications(Notifications):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)


class TopicalExamResults(Notifications):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, null=True, blank=True, on_delete=models.CASCADE)
    test = models.UUIDField()

    def __str__(self):
        return str(self.user)
    
class PaymentNotifications(Notifications):
    amount = models.PositiveIntegerField()
    subscription_type = models.CharField(max_length=10)
    beneficiaries = models.CharField(max_length=1000)

    def __str__(self):
        return str(self.user)

class AccountInquiries(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    message = models.TextField(max_length=500)

    def __str__(self):
        return str(self.user)


class Prompt(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    quiz = models.TextField(max_length=500)

    def __str__(self):
        return str(self.quiz)
    
class Completion(models.Model):
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    response = models.TextField(max_length=1500)

    def __str__(self):
        return str(self.prompt.user)

class RateLimiter(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE)
    tokens = models.PositiveIntegerField()
    image = models.PositiveIntegerField()
    speech = models.PositiveIntegerField()

    def __str__(self):
        return str(self.user)