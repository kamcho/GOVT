import random
import string
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from Finance.models import RawFeePayment, StudentFeePayment
from SubjectList.models import Subject
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from Teacher.models import StudentList
from Term.models import CurrentTerm, Exam, Grade, GradeModel, Terms
from django.contrib.messages import success,error
from Users.models import AcademicProfile, MyUser, StudentsFeeAccount



class AddSubjectScore(UserPassesTestMixin,TemplateView):
    template_name = 'Term/add_score.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            class_id = self.kwargs['class_id']
            subject_id= self.kwargs['subject']
            subject = Subject.objects.get(id=subject_id)
            term = CurrentTerm.objects.all().last()
            context['term'] = term
            excluded = Exam.objects.filter(subject=subject, term=term.term).values_list('user__email')

            students = AcademicProfile.objects.filter(current_class__class_id=class_id).exclude(user__email__in=excluded)
            
            context['subject'] = subject
            context['students'] = students
            scores = Exam.objects.filter(user__academicprofile__current_class__class_id=class_id, subject=subject, term__term=term).order_by('user__personalprofile__f_name')
            context['scores'] = scores
        except Exception as e:
            messages.error(self.request, 'An error occurered. Please contact @support')
        return context
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            if 'update' in request.POST:
                try:
                    score = request.POST.get('new')
                    if int(score) > 0 and int(score) <= 100:
                        user = request.POST.get('update')
                        term = CurrentTerm.objects.all().last()
                        subject = self.get_context_data().get('subject')
                        points = subject.get_grade(int(score))
                        exam = Exam.objects.get(user__email=user, subject=subject, term=term.term)
                        exam.score = score
                        exam.points = points[1]
                        exam.grade = points[0]
                        exam.save()
                        messages.success(request, f'Update was Successfull')
                    else:
                        messages.error(request, 'Marks can not be less than 0 nor exceed 100 ')
                except Exception as e:
                    messages.error(self.request, 'An error occured while try to update the marks!')
            else:
                
                score = int(request.POST.get('score'))
                if score > 0 and score <= 100:
                   
                    try:
                        email = request.POST.get('user')
                        user = MyUser.objects.get(email=email)
                        # grading = GradeModel.objects.filter(upper_limit__gte=score, lower_limit__lte=score).first()
                        term = CurrentTerm.objects.all().last()
                        subject = self.get_context_data().get('subject')
                        points = subject.get_grade(score)
                        exam = Exam.objects.create(user=user, subject=subject, score=score, points=points[1], grade=points[0] , term=term.term)
                        success = (self.request, f'Succesfully added marks for {user}. score = {score}')
                        request.session['exclude'] = email
                    except Exception as e:
                        error(request, 'An error occurred while trying to save marks')
                else:
                    messages.error(request, 'Marks can not be less than 0 nor exceed 100 ')

            return redirect(request.get_full_path())
    
    def test_func(self):
        term = CurrentTerm.objects.first()
        try:
            class_id = self.kwargs['class_id']
            subject= self.kwargs['subject']
            cls = StudentList.objects.get(user=self.request.user, class_id__class_id=class_id, subject__id=subject)
            return term.mode 
        except:
            return False
        



    
class TermListView(TemplateView):
    template_name = 'Term/terms_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        terms = Terms.objects.all().order_by('-starts_at')[:3]
        context['terms'] = terms
        if not terms:
            messages.info(self.request, 'There are no terms set in the database')

        return context
    
class TermInfo(TemplateView):
    template_name = 'Term/term_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            term_id = self.kwargs['term']
            term = Terms.objects.get(id=term_id)
            context['term'] = term
            current = CurrentTerm.objects.all().first()
            context['current'] = current
            print(current.term.id, term.id)
            if str(current.term.id) == str(term.id):
                context['is_current'] = True
            # test_exam()
        except Exception as e:
            messages.error(self.request, 'We could not find a result matching your query!')

        return context 
    
    def post(self, request, **kwargs):
        if request.method == 'POST':
            year = request.POST.get('year')
            term_ins = request.POST.get('term')
            starts_at = request.POST.get('start')
            
            ends_at = request.POST.get('end')
            term_id = self.kwargs['term']
            term = Terms.objects.get(id=term_id)

            if 'delete' in request.POST:
                command = self.request.POST.get('command')
                if command == 'delete':
                    term.delete()

                    return redirect('terms')
                else:
                    messages.error(self.request, 'Invalid command!')
                    return redirect(self.request.get_full_path())
            elif 'edit' in request.POST:
                try:
                    term_id = self.kwargs['term']
                    term = Terms.objects.get(id=term_id)
                    term.year = year
                    term.term = term_ins
                    term.starts_at = starts_at
                    term.ends_at = ends_at
                    term.save()
                except Exception as e:
                    messages.error(self.request, 'An error occured while trying to update term info!')
                return redirect(request.get_full_path())
            else:
                term_id = self.kwargs['term']
                term = Terms.objects.get(id=term_id)
                curre = CurrentTerm.objects.all().delete()
                cur_term = CurrentTerm.objects.create(term=term)

                return redirect(request.get_full_path())


# sc = Exam.objects.all().delete()
# def test_exam():

#     users = MyUser.objects.filter(role='Student', academicprofile__current_class__grade=4)
#     subjects = Subject.objects.filter(grade=4)
#     term=Terms.objects.get(year=2024, term='Term 1')
    
    # for subject in subjects:

    #     for user in users:
    #         ran = random.randint(12, 100)
    #         points = subject.get_grade(int(ran))
    #         grade = points[0]
    #         pt = points[1]
    #         exam = Exam.objects.create(user=user,term=term, subject=subject, score=ran, grade=grade, points=pt)
    #         print(exam)
    # return None
def generate_random_number(length):
    digits = string.digits
    return '254' + ''.join(random.choice(digits) for _ in range(length - len('254')))
def generate_random_string(length):
    letters_and_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))
def generate_adm(length):
    letters_and_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))
def test_exam():
    users = MyUser.objects.filter(role='Student')
    
    
    for user in users:
        # try:
        #     amount = random.randint(-22500, 52500)
        #     profile = StudentsFeeAccount.objects.create(user=user, balance=amount)
        # except:
        #     pass

        
        stk_count = random.randint(1, 3)
        for count in range(stk_count):
            profile = StudentsFeeAccount.objects.get(user=user)
            amount = random.randint(1500, 5500)
            receipt = generate_random_string(9)
            phone = generate_random_number(10)
            balance = profile.balance - amount
            profile.balance = balance
            profile.save()
            
            
           
            payment = RawFeePayment.objects.create(amount=amount, receipt=receipt, phone=phone, adm_no=user.adm_no)
            fee = StudentFeePayment.objects.create(user=user, transaction_id=payment, balance=balance)
