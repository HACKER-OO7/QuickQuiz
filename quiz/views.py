import base64
from collections import defaultdict
import json
import os,io
from django.shortcuts import get_object_or_404, render,redirect,reverse
from matplotlib import pyplot as plt
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from django.db.models import Q
from django.core.mail import send_mail
from teacher import models as TMODEL
from student import models as SMODEL
from teacher import forms as TFORM
from student import forms as SFORM
from django.contrib.auth.models import User



def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request,'quiz/index.html')


def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

def afterlogin_view(request):
    if is_student(request.user):      
        return redirect('student/student-dashboard')
                
    elif is_teacher(request.user):
        accountapproval=TMODEL.Teacher.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('teacher/teacher-dashboard')
        else:
            return render(request,'teacher/teacher_wait_for_approval.html')
    else:
        return redirect('admin-dashboard')



def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    dict={
    'total_student':SMODEL.Student.objects.all().count(),
    'total_teacher':TMODEL.Teacher.objects.all().filter(status=True).count(),
    'total_course':models.Course.objects.all().count(),
    'total_question':models.Question.objects.all().count(),
    }
    return render(request,'quiz/admin_dashboard.html',context=dict)

@login_required(login_url='adminlogin')
def admin_teacher_view(request):
    dict={
    'total_teacher':TMODEL.Teacher.objects.all().filter(status=True).count(),
    'pending_teacher':TMODEL.Teacher.objects.all().filter(status=False).count(),
    'salary':TMODEL.Teacher.objects.all().filter(status=True).aggregate(Sum('salary'))['salary__sum'],
    }
    return render(request,'quiz/admin_teacher.html',context=dict)

@login_required(login_url='adminlogin')
def admin_view_teacher_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=True)
    return render(request,'quiz/admin_view_teacher.html',{'teachers':teachers})


@login_required(login_url='adminlogin')
def update_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=TMODEL.User.objects.get(id=teacher.user_id)
    userForm=TFORM.TeacherUserForm(instance=user)
    teacherForm=TFORM.TeacherForm(request.FILES,instance=teacher)
    mydict={'userForm':userForm,'teacherForm':teacherForm}
    if request.method=='POST':
        userForm=TFORM.TeacherUserForm(request.POST,instance=user)
        teacherForm=TFORM.TeacherForm(request.POST,request.FILES,instance=teacher)
        if userForm.is_valid() and teacherForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            teacherForm.save()
            return redirect('admin-view-teacher')
    return render(request,'quiz/update_teacher.html',context=mydict)



@login_required(login_url='adminlogin')
def delete_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-teacher')




@login_required(login_url='adminlogin')
def admin_view_pending_teacher_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=False)
    return render(request,'quiz/admin_view_pending_teacher.html',{'teachers':teachers})


@login_required(login_url='adminlogin')
def approve_teacher_view(request,pk):
    teacherSalary=forms.TeacherSalaryForm()
    if request.method=='POST':
        teacherSalary=forms.TeacherSalaryForm(request.POST)
        if teacherSalary.is_valid():
            teacher=TMODEL.Teacher.objects.get(id=pk)
            teacher.salary=teacherSalary.cleaned_data['salary']
            teacher.status=True
            teacher.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-pending-teacher')
    return render(request,'quiz/salary_form.html',{'teacherSalary':teacherSalary})

@login_required(login_url='adminlogin')
def reject_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return HttpResponseRedirect('/admin-view-pending-teacher')

@login_required(login_url='adminlogin')
def admin_view_teacher_salary_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=True)
    return render(request,'quiz/admin_view_teacher_salary.html',{'teachers':teachers})




@login_required(login_url='adminlogin')
def admin_student_view(request):
    dict={
    'total_student':SMODEL.Student.objects.all().count(),
    }
    return render(request,'quiz/admin_student.html',context=dict)

@login_required(login_url='adminlogin')
def admin_view_student_view(request):
    students= SMODEL.Student.objects.all()
    return render(request,'quiz/admin_view_student.html',{'students':students})



@login_required(login_url='adminlogin')
def update_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=SMODEL.User.objects.get(id=student.user_id)
    userForm=SFORM.StudentUserForm(instance=user)
    studentForm=SFORM.StudentForm(request.FILES,instance=student)
    mydict={'userForm':userForm,'studentForm':studentForm}
    if request.method=='POST':
        userForm=SFORM.StudentUserForm(request.POST,instance=user)
        studentForm=SFORM.StudentForm(request.POST,request.FILES,instance=student)
        if userForm.is_valid() and studentForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            studentForm.save()
            return redirect('admin-view-student')
    return render(request,'quiz/update_student.html',context=mydict)



@login_required(login_url='adminlogin')
def delete_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=User.objects.get(id=student.user_id)
    user.delete()
    student.delete()
    return HttpResponseRedirect('/admin-view-student')


@login_required(login_url='adminlogin')
def admin_course_view(request):
    return render(request,'quiz/admin_course.html')


@login_required(login_url='adminlogin')
def admin_add_course_view(request):
    courseForm=forms.CourseForm()
    if request.method=='POST':
        courseForm=forms.CourseForm(request.POST)
        if courseForm.is_valid():        
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-course')
    return render(request,'quiz/admin_add_course.html',{'courseForm':courseForm})


@login_required(login_url='adminlogin')
def admin_view_course_view(request):
    courses = models.Course.objects.all()
    return render(request,'quiz/admin_view_course.html',{'courses':courses})

@login_required(login_url='adminlogin')
def delete_course_view(request,pk):
    course=models.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/admin-view-course')



@login_required(login_url='adminlogin')
def admin_question_view(request):
    return render(request,'quiz/admin_question.html')


@login_required(login_url='adminlogin')
def admin_add_question_view(request):
    questionForm=forms.QuestionForm()
    if request.method=='POST':
        questionForm=forms.QuestionForm(request.POST)
        if questionForm.is_valid():
            question=questionForm.save(commit=False)
            course=models.Course.objects.get(id=request.POST.get('courseID'))
            question.course=course
            question.save()       
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-question')
    return render(request,'quiz/admin_add_question.html',{'questionForm':questionForm})


@login_required(login_url='adminlogin')
def admin_view_question_view(request):
    courses= models.Course.objects.all()
    return render(request,'quiz/admin_view_question.html',{'courses':courses})

@login_required(login_url='adminlogin')
def view_question_view(request,pk):
    questions=models.Question.objects.all().filter(course_id=pk)
    return render(request,'quiz/view_question.html',{'questions':questions})

@login_required(login_url='adminlogin')
def delete_question_view(request,pk):
    question=models.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/admin-view-question')

@login_required(login_url='adminlogin')
def admin_view_student_marks_view(request):
    students= SMODEL.Student.objects.all()
    return render(request,'quiz/admin_view_student_marks.html',{'students':students})

@login_required(login_url='adminlogin')
def admin_view_marks_view(request,pk):
    courses = models.Course.objects.all()
    response =  render(request,'quiz/admin_view_marks.html',{'courses':courses})
    response.set_cookie('student_id',str(pk))
    return response

@login_required(login_url='adminlogin')
def admin_check_marks_view(request,pk):
    course = models.Course.objects.get(id=pk)
    student_id = request.COOKIES.get('student_id')
    student= SMODEL.Student.objects.get(id=student_id)

    results= models.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request,'quiz/admin_check_marks.html',{'results':results})
    




def aboutus_view(request):
    return render(request,'quiz/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'quiz/contactussuccess.html')
    return render(request, 'quiz/contactus.html', {'form':sub})



from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


#new Add


# @login_required(login_url='adminlogin')


# def admin_view_course_report(request, course_id):
#     course = get_object_or_404(models.Course, id=course_id)

#     # Retrieve all results for the current course
#     all_results = models.Result.objects.filter(exam=course).values('student_id', 'marks')

#     # Create a dictionary to store the highest marks for each student
#     student_marks = {}
#     for result in all_results:
#         student_id = result['student_id']
#         marks = result['marks']
        
#         # Keep track of the highest marks for each student
#         if student_id in student_marks:
#             student_marks[student_id] = max(student_marks[student_id], marks)
#         else:
#             student_marks[student_id] = marks

#     # Prepare leaderboard with student names and their highest marks
#     leaderboard = []
#     for student_id, marks in student_marks.items():
#         # Retrieve the student instance
#         student = models.Student.objects.get(id=student_id)
#         student_name = student.get_name  # Access the get_name property
#         leaderboard.append({
#             'student': student_name,
#             'marks': marks
#         })
    
#     # Sort leaderboard by marks in descending order
#     leaderboard = sorted(leaderboard, key=lambda x: x['marks'], reverse=True)
    
#     # Calculate the average marks
#     total_marks = sum(student_marks.values())
#     count = len(student_marks)
#     avg_score = total_marks / count if count > 0 else 0

#     # Prepare data for pie chart for question options
#     questions = models.Question.objects.filter(course=course)
#     question_stats = []

#     for question in questions:
#         file_name = f"response_{course_id}_{question.id}.json"
#         file_path = os.path.join(settings.BASE_DIR, 'response', file_name)
        
#         if os.path.exists(file_path):
#             with open(file_path, 'r') as file:
#                 response_data = json.load(file)
            
#             question_responses = response_data.get("questions", [])
#             stats = {
#                 'question_id': question.id,
#                 'question_text': question.question,
#                 'options': {opt: 0 for opt in ['Option1', 'Option2', 'Option3', 'Option4']},
#             }

#             # Count how many students selected each option
#             for response in question_responses:
#                 selected_option = response.get('selected_option')
#                 if selected_option in stats['options']:
#                     stats['options'][selected_option] += 1

#             question_stats.append(stats)

#     # Prepare context data for the template
#     context = {
#         'course': course,
#         'leaderboard': leaderboard,
#         'avg_score': avg_score,
#         'question_stats': question_stats,
#     }

#     return render(request, 'quiz/admin_view_course_report.html', context)



# A2
# @login_required(login_url='adminlogin')

# def admin_view_course_report(request, course_id):
#     course = get_object_or_404(models.Course, id=course_id)

#     # Retrieve all results for the current course
#     all_results = models.Result.objects.filter(exam=course).values('student_id', 'marks')

#     # Create a dictionary to store the highest marks for each student
#     student_marks = {}
#     for result in all_results:
#         student_id = result['student_id']
#         marks = result['marks']
        
#         # Keep track of the highest marks for each student
#         if student_id in student_marks:
#             student_marks[student_id] = max(student_marks[student_id], marks)
#         else:
#             student_marks[student_id] = marks

#     # Prepare leaderboard with student names and their highest marks
#     leaderboard = []
#     for student_id, marks in student_marks.items():
#         # Retrieve the student instance
#         student = models.Student.objects.get(id=student_id)
#         student_name = student.get_name  # Access the get_name property
#         leaderboard.append({
#             'student': student_name,
#             'marks': marks
#         })
    
#     # Sort leaderboard by marks in descending order
#     leaderboard = sorted(leaderboard, key=lambda x: x['marks'], reverse=True)
    
#     # Calculate the average marks
#     total_marks = sum(student_marks.values())
#     count = len(student_marks)
#     avg_score = total_marks / count if count > 0 else 0

#     # Prepare data for pie chart for question options
#     questions = models.Question.objects.filter(course=course)
#     question_stats = []

#     for question in questions:
#         file_name = f"response_{course_id}_{question.id}.json"
#         file_path = os.path.join(settings.BASE_DIR, 'response', file_name)
        
#         # Initialize options count
#         options_count = {opt: 0 for opt in ['Option1', 'Option2', 'Option3', 'Option4']}
        
#         if os.path.exists(file_path):
#             with open(file_path, 'r') as file:
#                 response_data = json.load(file)
            
#             question_responses = response_data.get("questions", [])
            
#             # Count how many students selected each option
#             for response in question_responses:
#                 selected_option = response.get('selected_option')
#                 if selected_option in options_count:
#                     options_count[selected_option] += 1

#         question_stats.append({
#             'question_id': question.id,
#             'question_text': question.question,
#             'options': options_count,
#         })

#     # Prepare context data for the template
#     context = {
#         'course': course,
#         'leaderboard': leaderboard,
#         'avg_score': avg_score,
#         'question_stats': question_stats,
#     }

#     return render(request, 'quiz/admin_view_course_report.html', context)




#A3
@login_required(login_url='adminlogin')
def admin_view_course_report(request, course_id):
    # Retrieve course
    course = get_object_or_404(models.Course, id=course_id)

    # Retrieve all results for the current course
    all_results = models.Result.objects.filter(exam=course).values('student_id', 'marks')

    # Create a dictionary to store the highest marks for each student
    student_marks = {}
    for result in all_results:
        student_id = result['student_id']
        marks = result['marks']
        
        # Keep track of the highest marks for each student
        if student_id in student_marks:
            student_marks[student_id] = max(student_marks[student_id], marks)
        else:
            student_marks[student_id] = marks

    # Prepare leaderboard with student names and their highest marks
    leaderboard = []
    for student_id, marks in student_marks.items():
        # Retrieve the student instance
        student = models.Student.objects.get(id=student_id)
        student_name = student.get_name  # Access the get_name property
        leaderboard.append({
            'student': student_name,
            'marks': marks
        })
    
    # Sort leaderboard by marks in descending order
    leaderboard = sorted(leaderboard, key=lambda x: x['marks'], reverse=True)
    
    # Calculate the average marks
    total_marks = sum(student_marks.values())
    count = len(student_marks)
    avg_score = total_marks / count if count > 0 else 0

    # Prepare data for pie chart for question options
    question_stats = []

    # Loop through all questions for this course
    questions = models.Question.objects.filter(course=course)

    # Initialize a dictionary to track the number of responses per option for each question
    for question in questions:
        file_name = f"response_{course_id}_{question.id}.json"
        file_path = os.path.join(settings.BASE_DIR, 'response', file_name)
        
        # Initialize options count and percentages for each question
        options_count = {opt: 0 for opt in ['Option1', 'Option2', 'Option3', 'Option4']}
        option_percentages = {opt: 0.0 for opt in ['Option1', 'Option2', 'Option3', 'Option4']}
        options_text = {
            'Option1': question.option1,
            'Option2': question.option2,
            'Option3': question.option3,
            'Option4': question.option4
        }

        # Loop through each response file for the course
        response_files = [f for f in os.listdir(os.path.join(settings.BASE_DIR, 'response')) if f.startswith(f"response_{course_id}_")]
        total_responses = 0  # Track total responses for the question
        
        for file_name in response_files:
            file_path = os.path.join(settings.BASE_DIR, 'response', file_name)
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    response_data = json.load(file)
                
                question_responses = response_data.get("questions", [])
                total_responses += len(question_responses)  # Accumulate total responses
                
                # Count how many students selected each option for this question
                for response in question_responses:
                    selected_option = response.get('selected_option')
                    question_id = response.get('question_id')
                    
                    # Ensure the option matches the correct "OptionX" format
                    if selected_option and selected_option in options_count:
                        options_count[selected_option] += 1
                        # Log each time an option is selected
                        print(f"Selected option: {selected_option} for Question ID {question_id}, Current count: {options_count[selected_option]}")
        
        # Calculate percentages for each option if there are responses
        if total_responses > 0:
            option_percentages = {
                option: (count / total_responses * 100) for option, count in options_count.items()
            }
        else:
            print(f"No valid responses to calculate percentages for Question ID {question.id}.")

        # Add question data with percentages and option text to question_stats
        question_stats.append({
            'question_id': question.id,
            'question_text': question.question,
            'options': options_count,
            'option_percentages': option_percentages,  # Add percentages
            'options_text': options_text,  # Add option text
        })

    # Prepare context data for the template
    context = {
        'course': course,
        'leaderboard': leaderboard,
        'avg_score': avg_score,
        'question_stats': question_stats,
    }

    # Print context to the console for debugging
    # print("Context Data:", context)

    return render(request, 'quiz/admin_view_course_report.html', context)

