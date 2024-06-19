import datetime
from django.contrib.auth import authenticate, login


from django.contrib.auth.hashers import make_password

from itertools import groupby
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import TemplateView

from Analytics.views import check_role
# from Finance.models import MpesaPayouts
from Finance.models import TermFeeStructure
from Guardian.models import MyKids
from Supervisor.models import ExtraCurricular, FeeMigrations, FileModel, Updates
from Teacher.models import StudentList
from Term.models import ClassTermRanking, CurrentTerm, Exam, Terms
from Users.models import AcademicProfile, MyUser, PersonalProfile, SchoolClass, StudentsFeeAccount
from Exams.models import ClassTest, ClassTestStudentTest, GeneralTest, StudentTest
from SubjectList.models import Subject, Subtopic, Course

def get_marks_distribution_data(grade, term, year):
    # Replace 'YourGradeModelField' with the actual field name representing the grade in your SchoolClass model
    grade_results = Exam.objects.filter(term__term=term,term__year=year, user__academicprofile__current_class__grade=grade).values('user__id').annotate(
        total_marks=Sum('score')
    ).order_by('total_marks')

    # Define the range size
    range_size = 20

    # Create a histogram of total marks in specified ranges
    marks_histogram = {}
    for result in grade_results:
        total_marks = result['total_marks']
        marks_range = (total_marks // range_size) * range_size
        marks_histogram[marks_range] = marks_histogram.get(marks_range, 0) + 1

    return marks_histogram
class SupervisorHomeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/supervisor_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # user = self.request.user

        users = MyUser.objects.all()
        val = users.filter(role='Student', personalprofile__gender='Male').count()
        context['users'] = users.count()
        context['males'] = users.filter(role='Student', personalprofile__gender='Male').count()
        context['females'] = users.filter(role='Student', personalprofile__gender='Female').count()

        context['t_males'] = users.filter(role='Teacher', personalprofile__gender='Male').count()
        context['t_females'] = users.filter(role='Teacher', personalprofile__gender='Female').count()
        context['g_males'] = users.filter(role='Guardian', personalprofile__gender='Male').count()
        context['g_females'] = users.filter(role='Guardian', personalprofile__gender='Female').count()
        context['students'] = users.filter(role='Student').count()
        context['teachers'] = users.filter(role='Teacher').count()
        context['parents'] = users.filter(role='Guardian').count()
        context['student_lst'] = users.filter(role='Student')[:10]
        
        grade_4_data = get_marks_distribution_data(4, 'Term 1', '2024')
        grade_5_data = get_marks_distribution_data(5, 'Term 1', '2024')
        grade_6_data = get_marks_distribution_data(6, 'Term 1', '2024')

# Preparing data for the bar chart
        labels = list(grade_5_data.keys())
        datasets = [
            {
                'label': 'Grade 4',
                'data': [grade_4_data.get(label, 0) for label in labels],
                'backgroundColor': 'rgba(0, 0, 0, 0.5)',
                'borderColor': 'rgba(0, 0, 0, 0.5)',
                'borderWidth': 2.5,
            },
            {
                'label': 'Grade 5',
                'data': [grade_5_data.get(label, 0) for label in labels],
                'backgroundColor': 'rgba(85, 133, 181)',
                'borderColor': 'rgba(85, 133, 181)',
                'borderWidth': 2.5,
            },
            {
                'label': 'Grade 6',
                'data': [grade_6_data.get(label, 0) for label in labels],
                'backgroundColor': 'rgba(255, 181, 181)',
                'borderColor': 'rgba(255, 181, 181)',
                'borderWidth': 2.5,
            }
        ]

        # Convert data to JSON for passing to the template
        chart_data = {
            'labels': labels,
            'datasets': datasets,
        }
        current_term = CurrentTerm.objects.filter().last()
        context['current_term'] = current_term
        context['chart_data'] = chart_data
        
        
        return context
    
    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            term = self.request.POST.get('term')
            year = self.request.POST.get('year')
            user = self.request.user

            grade_4_data = get_marks_distribution_data(4, term, year)
            grade_5_data = get_marks_distribution_data(5, term, year)
            grade_6_data = get_marks_distribution_data(6, term, year)

    # Preparing data for the bar chart
            labels = list(grade_6_data.keys())
            datasets = [
                {
                    'label': 'Grade 4',
                    'data': [grade_4_data.get(label, 0) for label in labels],
                    'backgroundColor': 'rgba(0, 0, 0, 0.5)',
                    'borderColor': 'rgba(0, 0, 0, 0.5)',
                    'borderWidth': 4,
                    
                },
                {
                    'label': 'Grade 5',
                    'data': [grade_5_data.get(label, 0) for label in labels],
                    'backgroundColor': 'rgba(0, 255, 0, 0.8)',
                    'borderColor': 'rgba(0, 255, 0, 1)',
                    'borderWidth': 4,
                },
                {
                    'label': 'Grade 6',
                    'data': [grade_6_data.get(label, 0) for label in labels],
                    'backgroundColor': 'rgba(255, 2, 2, 0.8)',
                    'borderColor': 'rgba(255, 2, 2, 1)',
                    'borderWidth': 4,
                }
            ]

            # Convert data to JSON for passing to the template
            chart_data = {
                'labels': labels,
                'datasets': datasets,
            }
            
            context = {
                'chart_data':chart_data,
                'users': self.get_context_data().get('users'),
                'students': self.get_context_data().get('students'),
                'teachers': self.get_context_data().get('teachers'),
                'parents': self.get_context_data().get('parents'),
                'student_lst': self.get_context_data().get('student_lst'),
                'term':term,
                'year':year,
                'current_term':self.get_context_data().get('current_term')

            }

            return render(self.request, self.template_name, context)
        
    def test_func(self):
        return self.request.user.role in ['Supervisor', 'Admin']


class ClassTestAnalytics(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/class_test_analytics.html'

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        class_id= self.kwargs['class_id']
        try:
            class_ins = SchoolClass.objects.get(class_id=class_id)
        except:
            messages.error(self.request, 'Invalid class id')
        
        if self.request.user.role == 'Student':
            # get the current logged in user(learner) current grade and associated Subjects
            context['base_html'] = 'Users/base.html'
        elif self.request.user.role == 'Guardian':
            context['base_html'] = 'Guardian/baseg.html'
        elif self.request.user.role == 'Teacher':
            context['base_html'] = 'Teacher/teachers_base.html'
        elif self.request.user.role in ['Supervisor', 'Finance']:
            context['base_html'] = 'Supervisor/base.html'

       
        current_term = CurrentTerm.objects.filter().last()
        context['classes'] = SchoolClass.objects.filter(grade=class_ins.grade)
        context['class'] = class_ins
        context['current_term'] = current_term
        context['term'] = 'Term 1'
        context['year'] = 2024


        return context
    
    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            term = self.request.POST.get('term')
            year = self.request.POST.get('year')

            context = {
                'classes':self.get_context_data().get('classes'),
                'class':self.get_context_data().get('class'),
                'term':term,
                'year':year,
                'base_html':self.get_context_data().get('base_html')
            }
            return render(self.request, self.template_name, context)


            


class SupervisorDashboard(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/admin_dashboard.html'

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        current_term = CurrentTerm.objects.all().first()
        if current_term:
            context['current_term'] = current_term
        else:
            context['current_term'] = False


        return context
    
    def test_func(self):
        return self.request.user.role == 'Supervisor'



class CreateUser(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/create_user.html'

    def get_context_data(self, **kwargs) :
        context = super().get_context_data(**kwargs)
        classes = SchoolClass.objects.all()
        context['classes'] = classes
        return context
    def test_func(self):
        return self.request.user.role == 'Supervisor'

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            try:
                email = request.POST.get('email')
                f_name = request.POST.get('f_name')
                l_name = request.POST.get('l_name')
                surname = request.POST.get('surname')
                role = request.POST.get('role')
                gender = request.POST.get('gender')
                fee = request.POST.get('fee')
                print(role,f_name)
                if role == 'Student':
                    class_id = request.POST.get('class')
                    user = MyUser.objects.create(email=email, role=role, password=make_password(email))
                    profile = PersonalProfile.objects.get(user=user)
                    print(class_id, '\n\n\n\n\n\n')
                    class_id = SchoolClass.objects.get(class_id=class_id)
                    profile.f_name = f_name
                    profile.l_name = l_name
                    profile.surname = surname
                    profile.gender = gender
                    profile.save()
                    academia = AcademicProfile.objects.get(user=user)
                    academia.current_class = class_id
                    class_id.class_size = class_id.class_size + 1
                    class_id.save()
                    academia.save()
                    created, fee_profile = StudentsFeeAccount.objects.get_or_create(user=user)
                    created.balance = fee
                    created.save()

                    return redirect('students-profile', email)
            
                else:
                    user = MyUser.objects.create(email=email, role=role, password=make_password(email))
                    profile = PersonalProfile.objects.get(user=user)
                    profile.f_name = f_name
                    profile.l_name = l_name
                    profile.surname = surname
                    profile.gender = gender
                    profile.save()
                    if role == 'Guardian':
                        return redirect('guardian-view', email)
                    else:
                        return redirect('teachers-profile', email)
            except IntegrityError as e:
               messages.error(self.request, str(e)) 
            except Exception as e:
                messages.error(self.request, f'{str(e)}eWe could not save the user. Contact @support')

            return redirect(request.get_full_path())





class LinkStudent(LoginRequiredMixin,  UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/link.html'

    def test_func(self):
        return self.request.user.role == 'Supervisor'
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            if 'verify' in self.request.POST:
                params = request.POST.get('search')
                print(params)
                adm = self.kwargs['adm']
                mykids = MyKids.objects.filter(kids__adm_no=adm)
                if params:
                    users = MyUser.objects.filter(Q(personalprofile__f_name__contains=params) | Q(personalprofile__l_name__contains=params)
                                                    | Q(personalprofile__surname__contains=params) | Q(email__contains=params), role='Guardian')
                    print(users)
                    context = {'parents':users,
                                'guardians':mykids,
                                'verified':True
                            }
                    

                    return render(self.request, self.template_name, context)
                else:
                    return redirect(self.request.get_full_path())        
            elif 'remove' in self.request.POST:
                pr = self.request.POST.get('remove')
                adm = self.kwargs['adm']
                std = MyUser.objects.get(adm_no=adm)
                mykkids = MyKids.objects.get(user__id=pr)
                mykkids.kids.remove(std)

                return redirect(self.request.get_full_path())
            else:
                parent = self.request.POST.get('names')
                adm = self.kwargs['adm']
                kid = MyUser.objects.get(adm_no=adm)
                pr = MyUser.objects.get(id=parent)
                mykids, create = MyKids.objects.get_or_create(user=pr)
                mykids.kids.add(kid)
                messages.success(self.request, 'Success')
        return redirect(self.request.get_full_path())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        adm = self.kwargs['adm']

        mykids = MyKids.objects.filter(kids__adm_no=adm)
        context['guardians'] = mykids
        return context
class StudentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/students_view.html'

    

    def get_context_data(self, **kwargs):
        context = super(StudentsView, self).get_context_data(**kwargs)
        user = self.request.user
        
        try:            
            users = MyUser.objects.filter(role='Student')[:15]
            


            
            context['users'] = users
            if not users:
                messages.error(self.request, 'We could not fetch students from the database')
           
        except Exception:
            messages.error(self.request, 'An error occured. Contact @support')
            
        return context
    
    def post(self,*args, **kwargs):
        if self.request.method == 'POST':
            params = self.request.POST.get('search')
                            
            if params:
                users = MyUser.objects.filter(Q(personalprofile__f_name__contains=params) | Q(personalprofile__l_name__contains=params)
                                                | Q(personalprofile__surname__contains=params) | Q(email__contains=params), role='Student')
                context = {'users':users}
                if not users:
                    messages.info(self.request, 'We could not find results matching your query !')
                return render(self.request, self.template_name, context)
            else:
                return redirect(self.request.get_full_path())
            
                
                
            
          
    def test_func(self):
        return self.request.user.role not in ['Student', 'Guardian']
        

class TeachersView(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/teachers_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            
            users  = MyUser.objects.filter(role='Teacher')
            context['users'] = users
        
        except Exception:
            messages.error(self.request, 'We could not fetch Teachers from the database')
        return context
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':

            params = request.POST.get('search')
           
            if params:
                users = MyUser.objects.filter(Q(personalprofile__f_name__contains=params) | Q(personalprofile__l_name__contains=params)
                                                | Q(personalprofile__surname__contains=params) | Q(email__contains=params), role='Teacher')
                context = {'users':users}
                return render(self.request, self.template_name, context)
            else:
                return redirect(self.request.get_full_path())                                                                   
                
        return redirect(self.request.get_full_path())


class GuardianListView(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/guardians_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            
            users  = MyUser.objects.filter(role='Guardian')
            context['users'] = users
        
        except Exception:
            messages.error(self.request, 'We could not fetch Teachers from the database')
        return context
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':

            params = request.POST.get('search')
           
            if params:
                users = MyUser.objects.filter(Q(personalprofile__f_name__contains=params) | Q(personalprofile__l_name__contains=params)
                                                | Q(personalprofile__surname__contains=params) | Q(email__contains=params), role='Guardian')
                context = {'users':users}
                return render(self.request, self.template_name, context)
            else:
                return redirect(self.request.get_full_path())                                                                   
                
        return redirect(self.request.get_full_path())

class TeachersProfile(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/teachers_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        email = self.kwargs['email']
        user = MyUser.objects.get(email=email)
        my_class = StudentList.objects.filter(user=user)
        context['classes'] = my_class
        context['teacher'] = user

        return context
    
class TeachersInfo(LoginRequiredMixin,TemplateView):
    template_name = 'Supervisor/teacher_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.kwargs['email']
        try:
            user = MyUser.objects.get(email=email)
            my_class = StudentList.objects.filter(user=user)
    
                # get teacher profile
        
            context['classes'] = my_class
            context['teacher'] = user
        except:
            messages.error(self.request, 'We could not find user matching query!')

        return context

class GuardianView(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/guardian_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.kwargs['email']
        try:
            context['guardian'] = MyUser.objects.get(email=email)
        except MyUser.DoesNotExist:
            messages.error(self.request, 'User does not exist !!')
        


        return context


class StudentProfile(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/students_profile.html'

    def get_context_data(self, **kwargs):
        context = super(StudentProfile, self).get_context_data(**kwargs)
        email = self.kwargs['email']
        try:
            user  = MyUser.objects.get(adm_no=email)
            guardians = MyKids.objects.filter(kids=user)
            context['guardians'] = guardians
            subjects = Subject.objects.filter(grade=4)
            context['subjects'] = subjects
            context['student'] = user
        except:
            messages.error(self.request, 'We could not find a user matching your query !')
        if self.request.user.role == 'Student':
            # get the current logged in user(learner) current grade and associated Subjects
            context['base_html'] = 'Users/base.html'
        elif self.request.user.role == 'Guardian':
            context['base_html'] = 'Guardian/baseg.html'
        elif self.request.user.role == 'Teacher':
            context['base_html'] = 'Teacher/teachers_base.html'
        elif self.request.user.role in ['Supervisor', 'Finance', 'Receptionist']:
            context['base_html'] = 'Supervisor/base.html'
        return context
    


    
class ManageStudent(UserPassesTestMixin, LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/manage_student.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        try:
            email = self.kwargs['email']
            student = MyUser.objects.get(adm_no=email)
            classes = SchoolClass.objects.all()
            context['classes'] = classes
            context['student'] = student
        except MyUser.DoesNotExist:
            messages.error(self.request, 'We could not find a user matching your query!')

        return context
    
    def post(self, request, **kwargs):
        if request.method == 'POST':
            email = request.POST.get('email')
            # adm = request.POST.get('adm_no')
            student = self.get_context_data().get('student')
            f_name = request.POST.get('f_name')
            l_name = request.POST.get('l_name')
            surname = request.POST.get('surname')
            class_id = request.POST.get('class')

            gender = request.POST.get('gender')
            try:
                if 'update' in request.POST:
                    adm = self.kwargs['email']
                    profile = PersonalProfile.objects.get(user=student)
                    st = MyUser.objects.get(adm_no=adm)
                    st.email = email
                    st.save()
                    if profile.user.role == 'Student':
                        class_id = SchoolClass.objects.get(class_id=class_id)
                        acd_profile = AcademicProfile.objects.get(user=student)
                        acd_profile.current_class = class_id
                        acd_profile.save()
                    profile.f_name = f_name
                    profile.l_name = l_name
                    profile.surname = surname
                    profile.gender = gender
                    profile.save()
                    messages.info(self.request, 'Update was successfull.')
                    

                    return redirect(request.get_full_path())
                elif 'delete' in request.POST:
                    user = MyUser.objects.get(email=email)
                    user.is_active = False
                    user.save()
                    messages.info(request, f'You have succesfully archived {user.personalprofile.get_names()} from Students Database')
                    return redirect(self.request.get_full_path())

                elif 'purge' in request.POST:
                    user = MyUser.objects.get(email=email)
                    messages.info(request, f'You have succesfully Deleted {user.personalprofile.get_names()} from Students Database')
                    user.delete()
                    return redirect('supervisor-home')
                else:
                    user = MyUser.objects.get(email=email)
                    user.is_active = True
                    user.save()
                    messages.success(request, f'You have succesfully restored {email} and all acount related data')
                    return redirect(self.request.get_full_path())
            except Exception as e:
                messages.error(self.request, str(e))
                return redirect(self.request.get_full_path())
            
    def test_func(self):
        return self.request.user.role == 'Supervisor'

                
            

class ArchivedUsers(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/archived_users.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = MyUser.objects.filter(is_active='False')
        context['users'] = users

        return context

    def test_func(self):
        return self.request.user.role == 'Supervisor'


            

class StudentExamProfile(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/students_exam_profile.html'

    def get_context_data(self, **kwargs):
        context = super(StudentExamProfile, self).get_context_data(**kwargs)
        context['base_html'] = check_role(self.request.user)
        print(check_role(self.request.user))
        email = self.kwargs['email']
        try:
            user  = MyUser.objects.get(email=email)
            grade = self.request.session.get('grade', 4)
            scores = Exam.objects.filter(user__email=email, subject__grade=grade) 
            term1 = scores.filter(term__term='Term 1')
            term2 = scores.filter(term__term='Term 2')
            term3 = scores.filter(term__term='Term 3')
            context['term1'] = term1
            context['term2'] = term2
            context['term3'] = term3
        except:
            messages.error(self.request, 'We could not find a student matching your query !')
        if self.request.user.role == 'Student':
            # get the current logged in user(learner) current grade and associated Subjects
            context['base_html'] = 'Users/base.html'
        elif self.request.user.role == 'Guardian':
            context['base_html'] = 'Guardian/baseg.html'
        elif self.request.user.role == 'Teacher':
            context['base_html'] = 'Teacher/teachers_base.html'
        elif self.request.user.role in ['Supervisor',  'Receptionist']:
            context['base_html'] = 'Supervisor/base.html'
        

        context['scores'] = scores
        context['grade'] = grade
        context['user'] = user
        return context
    
    # def test_func(self):
    #     return self.request.user.role == 'Supervisor'
    
    def post(self, *args, **kwargs):
      
        if self.request.method == 'POST':
            selected = self.request.POST.get('select')
           
            self.request.session['grade'] = selected

            return redirect(self.request.get_full_path())



class StudentTaskSelect(TemplateView):
    template_name = 'Supervisor/student_task_select.html'

    def get_context_data(self, **kwargs):
        context = super(StudentTaskSelect, self).get_context_data(**kwargs)
        email = self.kwargs['email']
        try:
            user  = MyUser.objects.get(email=email)
            context['user'] = user
        except:
            messages.error(self.request, 'We could not find a student matching your query !')
        return context


class StudentTestsView(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/students_test_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.kwargs['email']
        context['email'] = email
        tests = StudentTest.objects.filter(user__email=email)
        class_tests = ClassTestStudentTest.objects.filter(user__email=email)
        general_tests = GeneralTest.objects.filter(user__email=email)
        if not tests and not class_tests and not general_tests:
            messages.warning(self.request, 'This user has not taken any tests')
        
        context['class_tests'] = class_tests
        context['general_tests'] = general_tests
        context['tests'] = tests
        return context


class StudentTestDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/students_test_detail.html'

    def test_func(self):
        return self.request.user.role == 'Supervisor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.kwargs['email']
        test_id = self.kwargs['test_id']
        test_type = self.kwargs['test_type']
        try:
            if test_type == 'TopicalTest':
                test = StudentTest.objects.get(user__email=email, uuid=test_id)
                context['status'] = test.archived
            elif test_type == 'ClassTest':
                test = ClassTestStudentTest.objects.get(user__email=email, uuid=test_id)
                context['status'] = test.archived
            elif test_type == 'GeneralTest':
                test = GeneralTest.objects.get(user__email=email, uuid=test_id)
                context['status'] = test.archived
            else:
                messages.error(self.request, 'Invalid Test')
            context['test'] = test

        except :
            messages.error(self.request, 'We could not find this test')

        return context

    def post(self, *args, **kwargs):
        if self.request.method == "POST":

            try:
                if 'delete' in self.request.POST:
                    test_type = self.kwargs['test_type']
                    email = self.kwargs['email']
                    test_id = self.kwargs['test_id']
                    if test_type == 'TopicalTest':
                        test = StudentTest.objects.get(user__email=email, uuid=test_id)
                        test.archived = True
                        test.save()
                    elif test_type == 'ClassTest':
                        test = ClassTestStudentTest.objects.get(user__email=email, uuid=test_id)
                        test.archived = True
                        test.save()
                    elif test_type == 'GeneralTest':
                        test = GeneralTest.objects.get(user__email=email, uuid=test_id)
                        test.archived = True
                        test.save()
                    else:
                        messages.error(self.request, 'Invalid Test')
                elif 'restore' in self.request.POST:
                    test_type = self.kwargs['test_type']
                    email = self.kwargs['email']
                    test_id = self.kwargs['test_id']
                    if test_type == 'TopicalTest':
                        test = StudentTest.objects.get(user__email=email, uuid=test_id)
                        test.archived = False
                        test.save()
                    elif test_type == 'ClassTest':
                        test = ClassTestStudentTest.objects.get(user__email=email, uuid=test_id)
                        test.archived = False
                        test.save()
                    elif test_type == 'GeneralTest':
                        test = GeneralTest.objects.get(user__email=email, uuid=test_id)
                        test.archived = False
                        test.save()
                    else:
                        messages.error(self.request, 'Invalid Test')

            except:
                pass

            return redirect(self.request.get_full_path())
        
class CreateClass(TemplateView, LoginRequiredMixin):
    template_name = 'Supervisor/create_class.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['teachers'] = MyUser.objects.filter(role='Teacher')

        return context
    
    def post(self, *args, **kwargs):
        if self.request.method == "POST":
            class_name = self.request.POST.get('name')
            grade = self.request.POST.get('grade')
            class_size = self.request.POST.get('size')
            class_teacher = self.request.POST.get('teacher')
            class_teacher = self.get_context_data().get('teachers').get(email=class_teacher)
            try:
                school_class = SchoolClass.objects.create(class_name=class_name, grade=grade, class_size=class_size,
                                                           class_teacher=class_teacher)
                
                messages.success(self.request, f'{class_name} Has Been Added To Classes')
            except Exception as e:
                messages.error(self.request, str(e))
            return redirect(self.request.get_full_path())

            

class ClassesView(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/classes.html'

    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        classes = SchoolClass.objects.all().order_by('grade')

        if user.role == 'Teacher':
            context['base_html'] = 'Teacher/teachers_base.html'
            
        elif user.role in ['Supervisor']:
            context['base_html'] = 'Supervisor/base.html'
            
        context['classes'] = classes
        

        return context     

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            
            grade = self.request.POST.get('grade')
            classes = SchoolClass.objects.filter(Q(grade=grade))

            context = {
                'classes':classes,
                'base_html':self.get_context_data().get('base_html'),
            }

            return render(self.request, self.template_name, context)
        else:
            return redirect(self.request.get_full_path())
    

class ClassList(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/class_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_id = self.kwargs['class_id']
        class_ins = SchoolClass.objects.get(class_id=class_id)
        context['class'] = class_ins
        students = AcademicProfile.objects.filter(current_class=class_ins)
        context['students'] = students


        return context
class ClassDetail(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/class_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_id = self.kwargs['class_id']
        class_id = SchoolClass.objects.get(class_id=class_id)
        context['class'] = class_id
        
        
        subjects = Subject.objects.filter(grade=class_id.grade)
        context['subjects'] = subjects
        year = class_id.grade
            # print(subjects)
        term = CurrentTerm.objects.filter().first()
        if not term:
            term = Terms.objects.last()
        context['term'] = term
        context['grade'] = year

        if self.request.user.role == 'Teacher':
            context['base_html'] = 'Teacher/teachers_base.html'
        elif self.request.user.role in ['Supervisor']:
            context['base_html'] = 'Supervisor/base.html'
        
        
        return context
    
    def post(self, request, **args):
        if request.method == 'POST':
            year = request.POST.get('year')
            term = request.POST.get('term')
            subjects = Subject.objects.filter(grade=year)
            if self.request.user.role == 'Teacher':
                base_html = 'Teacher/teachers_base.html'
            elif self.request.user.role in ['Supervisor']:
                base_html = 'Supervisor/base.html'

            context = {
                'term':term,
                'grade':year,
                'subjects':subjects,
                'class':self.get_context_data().get('class'),
                'base_html':base_html,
            }


            return render(self.request, self.template_name, context)




class ClassStudentsRanking(LoginRequiredMixin, TemplateView):
    template_name='Supervisor/class_students_ranking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_id = self.kwargs['class_id']
        try:
            class_instance = SchoolClass.objects.get(class_id=class_id)
            grade = class_instance.grade
            term = 'Term 1'
            stream = self.request.session.get('stream', False)
            if self.request.user.role == 'Teacher':
                context['base_html'] = 'Teacher/teachers_base.html'
            elif self.request.user.role in ['Supervisor']:
                context['base_html'] = 'Supervisor/base.html'
            

            context['class_id'] = class_instance
        
            scores = (
            Exam.objects
            .filter(user__academicprofile__current_class__class_id=class_id, subject__grade=grade, term__term=term)
            .values('user__personalprofile__f_name', 'user__email', 'user__personalprofile__l_name', 'user__personalprofile__surname')  # Group by the user
            .annotate(total_score=Sum('score'))
            .order_by('-total_score', 'user')  # Order by total_score descending, user ascending
                )
            if scores:
                ranked_students = []
                current_rank = 0

                for key, group in groupby(scores, key=lambda student: student['total_score']):
                    score_group = list(group)
                    
                    # Assign the same rank to students with the same score
                    for student in score_group:
                        student['rank'] = current_rank + 1
                    
                    # Skip the following rank
                    current_rank += len(score_group)

                    # Append students to the result list
                    ranked_students.extend(score_group)
                    context['students'] = ranked_students
            # else:
            #     messages.info(self.request, f'{class_instance.class_name} grade {grade} {term} results not found!')
             
                
            subjects = Subject.objects.filter(grade=grade)
            context['subjects'] = subjects
            
            context['term'] = term
            context['grade'] = grade
        except Exception as e:
            messages.error(self.request, 'An error occured. Please contact @support')

            
        return context
    
    
    

    def post(self, request, **kwargs):
        if self.request.method == 'POST':
            grade = request.POST.get('year')
            term = request.POST.get('term')
            stream = request.POST.get('stream')
            print(f'stream {stream}')
            current_class = SchoolClass.objects.get(class_id=self.kwargs['class_id'])
            if stream == 'stream':

           
                class_id = SchoolClass.objects.filter(grade=current_class.grade)
                class_id = class_id.values_list('class_id')
                scores = (
                    Exam.objects
                    .filter(Q(user__academicprofile__current_class__class_id__in=class_id), Q(subject__grade=grade), Q(term__term=term))
                    .values('user__personalprofile__f_name', 'user__email','user__personalprofile__l_name', 'user__personalprofile__surname', 'user__academicprofile__current_class__class_name')  # Group by the user
                    .annotate(total_score=Sum('score'))
                    .order_by('-total_score', 'user')  # Order by total_score descending, user ascending
                )
                

                stream  = True
                inclusive = True
            else:

                class_id = current_class
                scores = (
                Exam.objects
                .filter(Q(user__academicprofile__current_class__class_id=class_id.class_id), Q(subject__grade=grade), Q(term__term=term))
                .values('user__personalprofile__f_name', 'user__email', 'user__personalprofile__l_name', 'user__personalprofile__surname', 'user__academicprofile__current_class__class_name')  # Group by the user
                .annotate(total_score=Sum('score'))
                .order_by('-total_score', 'user')  # Order by total_score descending, user ascending
            )
                stream = None
                inclusive = None
            ranked_students = []
            current_rank = 0

            for key, group in groupby(scores, key=lambda student: student['total_score']):
                score_group = list(group)
                
                # Assign the same rank to students with the same score
                for student in score_group:
                    student['rank'] = current_rank + 1
                
                # Skip the following rank
                current_rank += len(score_group)

                # Append students to the result list
                ranked_students.extend(score_group)
                    
            subjects = Subject.objects.filter(grade=grade)
            context = {
                'subjects':subjects,
                'students': ranked_students,
                'term':term,
                'stream':stream,
                'inclusive':inclusive,
                'schools':self.get_context_data().get('schools'),
                'grade':grade,
                'base_html':self.get_context_data().get('base_html'),
                'class_id':self.get_context_data().get('class_id'),
                
            }
            if not scores:
                messages.error(self.request, 'Results matching query were not found.')
            return render(self.request, self.template_name, context)


        return redirect(request.get_full_path())



def rank(marks_object):
        
    return marks_object

class PrintReport(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/print_card.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.kwargs['email']
        rank = self.kwargs['rank']
        grade = self.kwargs['grade']
        term = self.kwargs['term']
        results = Exam.objects.filter(user__email=email, subject__grade=grade, term__term=term)
        context['results'] = results
        context['rank'] = rank
        context['student'] = MyUser.objects.get(email=email)

        return context
    
class ClassSubjectDetail(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/class_subject_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_id = self.kwargs['class_id']
        class_name = SchoolClass.objects.get(class_id=class_id)
        subject = self.kwargs['subject']
        term = self.kwargs['term']
        try:
            term = Terms.objects.get(id=self.kwargs['term'])
        except:
            term = Terms.objects.filter(term=self.kwargs['term']).last()
        context['term'] = term
        scores = Exam.objects.filter(user__academicprofile__current_class__class_id=class_id, subject__id=subject, term__term=term).order_by('-score')
        context['tests'] = scores
        context['class'] = class_name
        if not scores:
            messages.info(self.request, f'{ class_name.class_name } { term } results not found!')
        if self.request.user.role == 'Teacher':
            context['base_html'] = 'Teacher/teachers_base.html'
        elif self.request.user.role in ['Supervisor']:
            context['base_html'] = 'Supervisor/base.html'
        return context
class TestTaskView(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/test_type_select.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def parse_quiz(request):
    # Parse data
    session_quiz_data = request.session.get('quiz')
    topic = session_quiz_data['topic']
    sub_topic = session_quiz_data['subtopic']
    quiz = session_quiz_data['quiz']
    session_selection_data = request.session.get('selection_info')
    selection1 = session_selection_data['selection1']
    selection2 = session_selection_data['selection2']
    selection3 = session_selection_data['selection3']
    selection4 = session_selection_data['selection4']
    return sub_topic, topic, quiz, selection1, selection2, selection3, selection4




class ManageClassTeacher(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/class_teacher.html'

    def test_func(self) :
        return self.request.user.role == 'Supervisor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        classes = SchoolClass.objects.all()
        teachers = MyUser.objects.filter(role='Teacher')
        context['classes'] = classes
        context['teachers'] = teachers

        return context
    
    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            class_id = self.request.POST.get('class')
            teacher = self.request.POST.get('user')
            teacher = MyUser.objects.get(email=teacher)
            class_instance = SchoolClass.objects.get(class_id=class_id)
            class_instance.class_teacher = teacher
            class_instance.save()
            messages.success(self.request, f'{teacher} is now class teacher of {class_instance.class_name}')

            return redirect(self.request.get_full_path())



class Promote(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/promote.html'

    def test_func(self):
        return self.request.user.role == 'Supervisor'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        classes = SchoolClass.objects.all()
        context['classes'] = classes

        return context
    
    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            classes = self.get_context_data().get('classes')
            pwd = self.request.POST.get('pwd')
            email = self.request.user.email
            user = authenticate(self.request, username=email, password=pwd)
            if user:
                if 'promote' in self.request.POST:
                    for class_ins in classes:
                        if class_ins.grade < 9:
                            class_ins.grade = class_ins.grade + 1
                        else:
                            class_ins.status = 'Graduated'
                        class_ins.save()
                    messages.success(self.request, 'You have succesfully promoted all students to the next grade')
            


                elif 'demote' in self.request.POST:
                    for class_ins in classes:
                        if class_ins.grade < 9:
                            class_ins.grade = class_ins.grade - 1
                        else:
                            class_ins.status = 'Active'
                        class_ins.save()
                    messages.success(self.request, 'You have succesfully demmoted all students to their previous grade')
            else:
                messages.error(self.request, 'Invalid password. Please try again or contact @support')


            return redirect(self.request.get_full_path())
        
class MigrateFees(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/migrate_fees.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        profiles = StudentsFeeAccount.objects.filter(user__is_active=True)
        context['all'] = MyUser.objects.filter(role='Student')
        context['students'] = profiles.count()
        context['balances'] = profiles.aggregate(totals=Sum('balance'))['totals']

        term = CurrentTerm.objects.all().first()
        if term:
            try:
                migration = FeeMigrations.objects.get(term=term.term)
                messages.error(self.request, 'You already made fee migrations for this term. @contact support!')
                context['error'] = True
                
            except :
                pass
        else:
            messages.info(self.request, 'You have not specified the current term!')
            context['error'] = True

        return context

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            term = CurrentTerm.objects.all().first()
            try:
                migration = FeeMigrations.objects.create(term=term.term, increment=0, current_balance=0, new_balances=0)
            except IntegrityError:
                messages.error(self.request, 'You already made fee migrations for this term. @contact support!')
                return redirect(self.request.get_full_path())
            structures = TermFeeStructure.objects.filter(term__term=term)
            if 'migrate' in self.request.POST:

                fee_profiles = StudentsFeeAccount.objects.filter(user__is_active=True)
                
                for profile in fee_profiles:
                    
                    try:
                        grade = profile.user.academicprofile.current_class.grade # type: ignore
                        debit = int(structures.get(grade=grade).amount)
                        new_balance = profile.balance + debit    
                        profile.balance = new_balance
                        profile.save()
                    
                    except:
                        pass
                messages.success(self.request, '100% fee migration')

            return redirect(self.request.get_full_path())

    def test_func(self):
        return self.request.user.role == 'Supervisor'
    
class Rollback(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/rollback.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        profiles = StudentsFeeAccount.objects.filter(user__is_active=True)
        context['all'] = MyUser.objects.filter(role='Student')
        context['students'] = profiles.count()
        context['balances'] = profiles.aggregate(totals=Sum('balance'))['totals']

        return context

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            term = CurrentTerm.objects.all().first()
            structures = TermFeeStructure.objects.filter(term__term=term)
            if 'migrate' in self.request.POST:

                fee_profiles = StudentsFeeAccount.objects.filter(user__is_active=True)
                
                for profile in fee_profiles:
                    
                    try:
                        grade = profile.user.academicprofile.current_class.grade # type: ignore
                        debit = int(structures.get(grade=grade).amount)
                        new_balance = profile.balance + debit    
                        profile.balance = new_balance
                        profile.save()
                    
                    except:
                        pass

            return redirect(self.request.get_full_path())

    def test_func(self):
        return self.request.user.role == 'Supervisor'


class CreateNotice(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/create_notice.html'

    def test_func(self):
        return self.request.user.role == 'Supervisor'

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            
            title = self.request.POST.get('title')
            description = self.request.POST.get('description')
            pdf = self.request.FILES.get('pdf')

            update = Updates.objects.create(title=title, description=description, file=pdf)

            return redirect('notice-id', update.id)
        

class Notices(TemplateView):
    template_name = 'Supervisor/notices.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['updates'] = Updates.objects.all().order_by('-date')

        if self.request.user.role == 'Student':
            # get the current logged in user(learner) current grade and associated Subjects
            context['base_html'] = 'Users/base.html'
        elif self.request.user.role == 'Guardian':
            context['base_html'] = 'Guardian/baseg.html'
        elif self.request.user.role == 'Teacher':
            context['base_html'] = 'Teacher/teachers_base.html'
        elif self.request.user.role in ['Supervisor', 'Finance','Receptionist']:
            context['base_html'] = 'Supervisor/base.html'

        return context

class NoticeID(TemplateView):
    template_name = 'Supervisor/notice_id.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        notice_id = self.kwargs['notice_id']
        context['notice'] = Updates.objects.get(id=notice_id)


        return context
    
    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            if 'delete' in self.request.POST:
                command = self.request.POST.get('command')
                if command == 'delete':
                    update = self.get_context_data().get('notice')
                    update.delete()
                    messages.error(self.request, 'You have succesfully deleted a notice update')

                    return redirect('notices')
                else:
                    messages.error(self.request, 'Invalid Command !')

                    return redirect(self.request.get_full_path())
            else:

            
                title = self.request.POST.get('title')
                description = self.request.POST.get('description')
                pdf = self.request.FILES.get('pdf')

                update = self.get_context_data().get('notice')
                update.title = title
                update.description = description
                update.file = pdf
                update.save()
                messages.success(self.request, 'Update was succesfull.')

                return redirect(self.request.get_full_path())
            

class AddActivity(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/create_activity.html'

    def test_func(self):
        return self.request.user.role == 'Teacher'

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            title = self.request.POST.get('title')
            description = self.request.POST.get('description')
            self.request.session['activity'] = {
            'title': title,
            'description': description,
        }



            return redirect('add-students')


    

class AddStudents(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/add_students.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['users'] = MyUser.objects.filter(role='Student')
        context['classes'] = StudentList.objects.filter(user=self.request.user)
        students = MyUser.objects.filter(id__in=self.request.session.get('students', []))
        if students:
            context['students'] = students

        
            

        
        return context
    
    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            class_id = self.request.POST.get('class')
            search = self.request.POST.get('search')
            if 'add' in self.request.POST:
                students = self.request.POST.getlist('user')
                existing_students = set(self.request.session.get('students', []))
    
    # Filter out duplicate values
                new_students = list(set(students) - existing_students)
                
                # Append new values to the existing list
                updated_students = existing_students.union(new_students)
                
                # Update the session key with the combined list
                self.request.session['students'] = list(updated_students)
                context = {'users':self.get_context_data().get('users'),
                           'classes':self.get_context_data().get('classes'),
                           'students':MyUser.objects.filter(id__in=self.request.session.get('students', []))
                           
                           }
                # context['students'] = self.request.session.get('students',None)
                
                return render(self.request, self.template_name, context)
            elif 'delete' in self.request.POST:
                id_to_delete = self.request.POST.get('delete')
                if id_to_delete in self.request.session['students']:
            # Remove the id_to_delete from the list
                    self.request.session['students'].remove(id_to_delete)
                    self.request.session.modified = True 
                    context = {'users':self.get_context_data().get('users'),
                           'classes':self.get_context_data().get('classes'),
                           'students':MyUser.objects.filter(id__in=self.request.session.get('students', []))
                           
                           }

                    return render(self.request, self.template_name, context)
                else:
                    return redirect(self.request.get_full_path())

            else:
                if class_id:
                    users = MyUser.objects.filter(academicprofile__current_class__class_id=class_id)

                    context = {
                        'users':users,
                        'classes':self.get_context_data().get('classes'),
                        'students':self.get_context_data().get('students'),
                    }

                    return render(self.request, self.template_name, context)

                if search:
                    users = MyUser.objects.filter(Q(personalprofile__f_name__contains=search) | Q(personalprofile__l_name__contains=search)
                                                        | Q(personalprofile__surname__contains=search) | Q(email__contains=search) )
                    context = {'users':users,
                            'classes':self.get_context_data().get('classes'),
                            }
                    return render(self.request, self.template_name, context)
                
                else:
                    return redirect(self.request.get_full_path())


class AddFiles(TemplateView):
    template_name = 'Supervisor/add_files.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['students'] = MyUser.objects.filter(id__in=self.request.session.get('students', []))
        context['activity'] = self.request.session.get('activity', [])

        if self.request.user.role == 'Teacher':
            context['base_html'] = 'Teacher/teachers_base.html'
        elif self.request.user.role == 'Supervisor':
            context['base_html'] = 'Supervisor/base.html'


        return context
    
    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            uploaded_files = self.request.FILES.getlist('files')
            title = self.get_context_data().get('activity')
            description = self.get_context_data().get('activity')
            students = self.get_context_data().get('students')

            activity = ExtraCurricular.objects.create(
                user=self.request.user,
                title = title['title'],
                description = description['description']
            )
            activity.students.add(*students)

            # Save each file to the database and associate it with the activity
            for file in uploaded_files:
                file_instance = FileModel.objects.create(file=file)
                
                activity.files.add(file_instance)

            return redirect('view-activity', activity.id)



class ViewActivities(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/view_activities.html'

    def get_context_data(self, **kwargs):
        role = self.request.user.role
        context = super().get_context_data(**kwargs)
        if role == 'Teacher':
            context['template'] = 'Teacher/teachers_base.html'
        else:
            context['template'] = 'Supervisor/base.html'

        
        context['activities'] = ExtraCurricular.objects.all().order_by('-date')

        return context
    
class ViewActivity(LoginRequiredMixin, TemplateView):
    template_name = 'Supervisor/view_activity.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        activity_id = self.kwargs['activity_id']
        activity = ExtraCurricular.objects.get(id=activity_id)
        context['activity'] = activity
        if self.request.user.role == 'Teacher':
            context['base_html'] = 'Teacher/teachers_base.html'
        elif self.request.user.role == 'Supervisor':
            context['base_html'] = 'Supervisor/base.html'
        elif self.request.user.role == 'Guardian':
            context['base_html'] = 'Guardian/baseg.html'
        elif self.request.user.role == 'Student':
            context['base_html'] = 'Users/base.html'
        



        return context

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            command = self.request.POST.get('option').lower()
            if command == 'delete':
                activity = self.get_context_data().get('activity')
                activity.delete()

                return redirect('activities')
            messages.error(self.request, 'Invalid Command')
            
            return redirect(self.request.get_full_path())
        
class ExamMode(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Supervisor/enable_exam_mode.html'

    def test_func(self):
        return self.request.user.role == 'Supervisor'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        mode = CurrentTerm.objects.all().first()
        context['mode'] = mode

        return context
    
    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            command = self.request.POST.get('action')
            mode = self.get_context_data().get('mode')
            if command == 'enable':
                inp = True
            else:
                inp = False

            mode.mode = inp
            mode.save()



            return redirect(self.request.get_full_path())
        
class AssignmentsView(TemplateView):
    template_name = 'Supervisor/assignments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignments = ClassTest.objects.all().order_by('-date')
        context['assignments'] = assignments
        context['users'] = MyUser.objects.filter(role='Teacher')
        context['subjects'] = Course.objects.all()

        return context

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            grade = self.request.POST.get('grade')
            subject = self.request.POST.get('subject')
            user = self.request.POST.get('user')
            start = self.request.POST.get('from')
            to = self.request.POST.get('to')
            status = self.request.POST.get('status')
            search = {}
            if grade:
                search['subject__grade'] = grade
            if subject:
                search['subject__course'] = subject
            if user:
                search['teacher'] = user
            if start:
                search['date__gte'] = start
            if to:
                search['date__lte'] = to
            if status:
                if status == 'active':
                    search['expiry__gt'] = datetime.datetime.now()
                else:
                    search['expiry__lt'] = datetime.datetime.now()
            tests = ClassTest.objects.filter(**search)
            context = {
                'assignments':tests,
                'users':self.get_context_data().get('users'),
                'subjects': self.get_context_data().get('subjects'),
            }
            return render(self.request, self.template_name, context)