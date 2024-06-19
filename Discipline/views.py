
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.contrib import messages
from Discipline.models import ClassIncident, IncidentBooking, StudentDisciplineScore
from Supervisor.models import ExtraCurricular
from Users.models import MyUser
# Create your views here.

def deductPoints(user, score):
    profile = StudentDisciplineScore.objects.get(user=user)
    if int(score) >= int(profile.points):
        profile.points = 0
    else:
        profile.points = profile.points - score
    profile.save()

    return None

def restorePoints(user, score):
    profile = StudentDisciplineScore.objects.get(user=user)
    profile.points = profile.points + score
    profile.save()

    return None
class CreateClassIncident(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Discipline/create_incident.html'
    
    def test_func(self) :
        return self.request.user.role == 'Supervisor'

    def post(self, request, **kwargs):
        if request.method == 'POST':
            name = request.POST.get('name')
            description = request.POST.get('description')
            degree = request.POST.get('degree')
            score = request.POST.get('points')
            try:
                incident = ClassIncident.objects.create(name=name, incident_degree=degree, description=description, points=score )
                messages.info(self.request, 'Success')

                return redirect('manage-incident', incident.id)
            except Exception as e:
                messages.error(self.request, 'An error occured. Please try again!')

            return redirect(request.get_full_path())

class Incidents(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Discipline/incidents.html'
    def test_func(self) :
        return self.request.user.role == 'Supervisor'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template'] = 'Supervisor/base.html'
        incidents = ClassIncident.objects.all().order_by('-points')
        context['incidents'] = incidents
        return context
    
class ManageIncident(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Discipline/manage_incident.html'

    def test_func(self) :
        return self.request.user.role in ['Supervisor', 'Teacher']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        incident_id = self.kwargs['id']
        role = self.request.user.role
        if role == 'Teacher':
            incidents = IncidentBooking.objects.filter(booked_by=self.request.user).order_by('-date')
            context['template'] = 'Teacher/teachers_base.html'
        else:
            incidents = IncidentBooking.objects.all().order_by('date')
            context['template'] = 'Supervisor/base.html'
        context['incidents'] = incidents
        try:
            incident = ClassIncident.objects.get(id=incident_id)
            context['incident'] = incident
        except ClassIncident.DoesNotExist:
            messages.error(self.request, 'Incident With The Given ID Does Not Exist!')
        return context
    
    def post(self, request, **kwargs):
        if request.method == 'POST':
            name = request.POST.get('name')
            description = request.POST.get('description')
            degree = request.POST.get('degree')
            score = request.POST.get('points')
            incident = self.get_context_data().get('incident')
            try:
                if 'update' in request.POST:
                    incident.name = name
                    incident.description = description
                    incident.incident_degree = degree
                    incident.points = score
                    incident.save()
                    messages.success(request, 'SUCCESS !')
                    return redirect(request.get_full_path())
                else:
                    command = self.request.POST.get('command')
                    if command == 'delete':
                        incident = incident.delete()
                        messages.success(request, 'SUCCESS !')
                        return redirect('incidents')
                    else:
                        messages.error(self.request, 'Invalid Command!')
                        return redirect(self.request.get_full_path())
            except Exception as e:
                messages.error(self.request, 'An error occured. Please try again !')
                return redirect(self.request.get_full_path())


class BookedIncidents(LoginRequiredMixin,  TemplateView):
    template_name = 'Discipline/booked_students.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        role = self.request.user.role
        if role == 'Teacher':
            incidents = IncidentBooking.objects.filter(booked_by=self.request.user).order_by('-date')
            context['template'] = 'Teacher/teachers_base.html'
        else:
            incidents = IncidentBooking.objects.all().order_by('date')
            context['template'] = 'Supervisor/base.html'
            context['suspended'] = StudentDisciplineScore.objects.filter(points__lte=0, user__is_active=True)
        context['incidents'] = incidents
        return context
    
class ManageBookedIncident(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'Discipline/manage_booked_incident.html'
    def test_func(self):
        return self.request.user.role in ['Supervisor', 'Teacher']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        incident_id = self.kwargs['id']
        role = self.request.user.role
        if role == 'Teacher':
            context['template'] = 'Teacher/teachers_base.html'
        else:
            context['template'] = 'Supervisor/base.html'
        try:
            incident = IncidentBooking.objects.get(id=incident_id)
            context['incidents'] = ClassIncident.objects.all().order_by('-points')
            context['incident'] = incident
        except:
            messages.error(self.request, 'Object not found!')
        return context
    

    
    def post(self, request, **kwargs):
        if request.method == 'POST':
            incident = self.get_context_data().get('incident')
            try:
                if 'delete' in request.POST:
                    incident.delete()
                    restorePoints(incident.user, incident.incident.points)
                    return redirect('booked-students')
                else:
                    name = request.POST.get('name')
                    name = ClassIncident.objects.get(id=name)
                    print(name.points,  incident.incident.points)
                    points = incident.incident.points - name.points 
                    restorePoints(incident.user, points)
                    incident.incident = name
                    incident.save()

                    return redirect(request.get_full_path())
            except Exception as e:
                messages.error(self.request, 'An error occured. Please try again!')
    

class StudentsDisciplineProfile(LoginRequiredMixin, TemplateView):
    template_name = 'Discipline/students_discipline.html'

    def post(self, *args, **kwargs):
        if self.request.method == 'POST':
            profile = self.get_context_data().get('profile')
            profile.points = 100
            profile.save()

            return redirect(self.request.get_full_path())
        

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.kwargs['email']
        try:
            l_user = MyUser.objects.get(email=email)
            incidents = IncidentBooking.objects.filter(user__email=email)
            context['incidents'] = incidents
            curricular = ExtraCurricular.objects.filter(students=l_user)
            context['events'] = curricular
            print(curricular)
            if not incidents:
                messages.info(self.request, 'This student does not have any Indiscipline incidents.')
        
    
            profile = StudentDisciplineScore.objects.get(user__email=email)
            context['profile'] = profile
        except StudentDisciplineScore.DoesNotExist:
            try:
                user = MyUser.objects.get(email=email)
                profile = StudentDisciplineScore.objects.create(user=user)
                context['profile'] = profile
            except MyUser.DoesNotExist:
                messages.error(self.request, 'We could not find any users matching your query !')
        role = self.request.user.role
        if role == 'Teacher':
            context['template'] = 'Teacher/teachers_base.html'
        elif role == 'Student':
            context['template'] = 'Users/base.html'
        elif role in ['Supervisor', 'Receptionist', 'Finance']:
            context['template'] = 'Supervisor/base.html'
        elif role == 'Guardian':
            context['template'] = 'Guardian/baseg.html'
        return context


    

class BookIncident(LoginRequiredMixin, TemplateView):
    template_name = 'Discipline/book_incident.html'


    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        classes = ClassIncident.objects.all().order_by('-points')
        context['classes'] = classes
        return context
    
    def post(self, request, **kwargs):
        if request.method == 'POST':
            adm_no = request.POST.get('adm_no')
            adm = request.POST.get('adm')
            recepient = request.POST.get('recipient')
            incident = request.POST.get('incident')
            teacher = request.user
            try:
                
                if 'verify' in request.POST:
                    student = MyUser.objects.get(adm_no=adm_no, role='Student')
                    context = {
                        'student': student,
                        'classes': self.get_context_data().get('classes'),}
                    return render(request, self.template_name, context=context)
                else:
                    print(adm)
                    student = MyUser.objects.get(adm_no=adm)
                    incident = ClassIncident.objects.get(id=incident)
                    booking = IncidentBooking.objects.create(user=student, incident=incident, booked_by=teacher)
                    deductPoints(student, incident.points)
                    messages.success(request, 'Incident Report was Succesful')
              
                return redirect(request.get_full_path())
                
            except MyUser.DoesNotExist as e:
                messages.error(request, str(e))
                return redirect(request.get_full_path())
           


        return redirect(request.get_full_path())