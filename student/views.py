from django.shortcuts import render,redirect,reverse , get_object_or_404
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from quiz import models as QMODEL
from teacher import models as TMODEL
import json,os
from django.db.models import Max



#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'student/studentclick.html')

def student_signup_view(request):
    userForm=forms.StudentUserForm()
    studentForm=forms.StudentForm()
    mydict={'userForm':userForm,'studentForm':studentForm}
    if request.method=='POST':
        userForm=forms.StudentUserForm(request.POST)
        studentForm=forms.StudentForm(request.POST,request.FILES)
        if userForm.is_valid() and studentForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            student=studentForm.save(commit=False)
            student.user=user
            student.save()
            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)
        return HttpResponseRedirect('studentlogin')
    return render(request,'student/studentsignup.html',context=mydict)

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_dashboard_view(request):
    dict={
    
    'total_course':QMODEL.Course.objects.all().count(),
    'total_question':QMODEL.Question.objects.all().count(),
    }
    return render(request,'student/student_dashboard.html',context=dict)

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_exam_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_exam.html',{'courses':courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def take_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    total_questions=QMODEL.Question.objects.all().filter(course=course).count()
    questions=QMODEL.Question.objects.all().filter(course=course)
    total_marks=0
    for q in questions:
        total_marks=total_marks + q.marks
    
    return render(request,'student/take_exam.html',{'course':course,'total_questions':total_questions,'total_marks':total_marks})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def start_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    questions=QMODEL.Question.objects.all().filter(course=course)
    if request.method=='POST':
        pass
    response= render(request,'student/start_exam.html',{'course':course,'questions':questions})
    response.set_cookie('course_id',course.id)
    return response

#OG
# @login_required(login_url='studentlogin')
# @user_passes_test(is_student)
# def calculate_marks_view(request):
#     if request.COOKIES.get('course_id') is not None:
#         course_id = request.COOKIES.get('course_id')
#         course=QMODEL.Course.objects.get(id=course_id)
        
#         total_marks=0
#         questions=QMODEL.Question.objects.all().filter(course=course)
#         for i in range(len(questions)):
            
#             selected_ans = request.COOKIES.get(str(i+1))
#             actual_answer = questions[i].answer
#             if selected_ans == actual_answer:
#                 total_marks = total_marks + questions[i].marks
#         student = models.Student.objects.get(user_id=request.user.id)
#         result = QMODEL.Result()
#         result.marks=total_marks
#         result.exam=course
#         result.student=student
#         result.save()

#         return HttpResponseRedirect('view-result')

#A1
# @login_required(login_url='studentlogin')
# @user_passes_test(is_student)
# def calculate_marks_view(request):
#     if request.COOKIES.get('course_id') is not None:
#         course_id = request.COOKIES.get('course_id')
#         course = QMODEL.Course.objects.get(id=course_id)
        
#         total_marks = 0
#         questions = QMODEL.Question.objects.filter(course=course)
        
#         selected_answers = {}
        
#         for i, question in enumerate(questions, start=1):
#             question_id = str(i)
#             selected_ans = request.COOKIES.get(question_id)
#             actual_answer = question.answer
#             selected_answers[question_id] = selected_ans
            
#             if selected_ans == actual_answer:
#                 total_marks += question.marks

#         student = QMODEL.Student.objects.get(user_id=request.user.id)
#         file_name = f"{course_id}_{student.id}.json"
#         file_path = os.path.join(settings.BASE_DIR, 'selected_answers', file_name)

#         os.makedirs(os.path.dirname(file_path), exist_ok=True)
#         with open(file_path, 'w') as file:
#             json.dump(selected_answers, file, indent=4)

#         result = QMODEL.Result(marks=total_marks, exam=course, student=student)
#         result.save()

#         print(f"Selected answers for student ID {student.id} in exam ID {course_id}:")
#         print(selected_answers)

#         return HttpResponseRedirect('view-result')





#A2


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def calculate_marks_view(request):
    if request.COOKIES.get('course_id') is not None:
        course_id = request.COOKIES.get('course_id')
        course = QMODEL.Course.objects.get(id=course_id)
        
        total_marks = 0
        correct_question = 0
        questions = QMODEL.Question.objects.filter(course=course)
        total_que = questions.count()
        
        question_data = []

        for i, question in enumerate(questions, start=1):
            question_id = str(i)
            selected_ans = request.COOKIES.get(question_id)
            actual_answer = question.answer
            
            is_correct = selected_ans == actual_answer
            if is_correct:
                total_marks += question.marks
                correct_question += 1
            
            # Collecting data for each question
            question_data.append({
                "question_id": question_id,
                "question_text": question.question,
                "options": {
                    "option1": question.option1,
                    "option2": question.option2,
                    "option3": question.option3,
                    "option4": question.option4
                },
                "correct_option": question.answer,
                "selected_option": selected_ans,
                "question_status": is_correct
            })

        student = QMODEL.Student.objects.get(user_id=request.user.id)
        response_data = {
            "course_id": course_id,
            "total_que": total_que,
            "student_id": student.id,
            "obtain_marks": total_marks,
            "correct_question": correct_question,
            "questions": question_data
        }

        # File path for storing JSON response
        file_name = f"response_{course_id}_{student.id}.json"
        file_path = os.path.join(settings.BASE_DIR, 'response', file_name)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write response data to JSON file
        with open(file_path, 'w') as file:
            json.dump(response_data, file, indent=4)

        # Save the result in the database
        result = QMODEL.Result(marks=total_marks, exam=course, student=student)
        result.save()

        # print(f"Response for student ID {student.id} in exam ID {course_id} saved to {file_name}")

        return HttpResponseRedirect('view-result')








@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_result_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/view_result.html',{'courses':courses})
    

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def check_marks_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    results= QMODEL.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request,'student/check_marks.html',{'results':results})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_marks_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_marks.html',{'courses':courses})




#added new 

# #added new 
# @login_required(login_url='studentlogin')
# @user_passes_test(is_student)
# def student_marks_report(request, exam_id):
#     # Retrieve the specific Result object and related questions for the selected exam
#     result = get_object_or_404(QMODEL.Result, id=exam_id)
#     questions = QMODEL.Question.objects.filter(course=result.exam)

#     # Collect question data along with correct answers and the student's selected answers
#     question_data = []
#     for question in questions:
#         # Placeholder logic for user's selected answer, replace with actual logic
#         user_answer = ""  # Fetch or calculate the student's selected answer for each question
#         question_data.append({
#             'text': question.question,
#             'option1': question.option1,
#             'option2': question.option2,
#             'option3': question.option3,
#             'option4': question.option4,
#             'answer': question.answer,
#             'user_answer': user_answer,
#             'is_correct': user_answer == question.answer
#         })
    
#     # Placeholder for performance comparison and rank, replace with actual logic
#     performance_data = {}  # Use actual data for performance comparison
#     rank = 1  # Calculate student's rank among other students if applicable

#     # Pass all relevant data to the template context
#     context = {
#         'exam': result.exam,
#         'result': result,
#         'questions': question_data,
#         'performance_data': performance_data,
#         'rank': rank,
#     }

#     return render(request, 'student/student_marks_report.html', context)


#A2
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_marks_report(request, exam_id):
    # Retrieve the specific Result object for the current student and exam
    result = get_object_or_404(QMODEL.Result, id=exam_id)
    student_id = result.student.id
    course_id = result.exam.id

    # Load responses from JSON file
    file_name = f"response_{course_id}_{student_id}.json"
    file_path = os.path.join(settings.BASE_DIR, 'response', file_name)
    if not os.path.exists(file_path):
        raise Http404("Response file not found for this exam.")

    with open(file_path, 'r') as file:
        response_data = json.load(file)

    # Extract question data
    question_data = response_data.get("questions", [])
    
    # Retrieve all results for the current course and only the highest marks per student
    all_results = QMODEL.Result.objects.filter(exam=course_id).values('student_id').annotate(highest_marks=Max('marks')).order_by('-highest_marks')
    
    # Convert all_results to a list of dictionaries with 'student_id' and 'highest_marks'
    all_results_list = list(all_results)
    
    # Find the current student's rank based on the highest marks
    rank = next((index + 1 for index, res in enumerate(all_results_list) if res['student_id'] == student_id), None)

    # Calculate the average marks
    total_marks = sum(res['highest_marks'] for res in all_results_list)
    count = len(all_results_list)
    avg_score = total_marks / count if count > 0 else 0

    # Prepare data for bar plot: student ID vs. obtained marks
    student_ids = [res['student_id'] for res in all_results_list]
    marks = [res['highest_marks'] for res in all_results_list]

    # Prepare context data for template
    context = {
        'exam': result.exam,
        'result': result,
        'questions': question_data,
        'rank': rank,
        'avg_score': avg_score,
        'student_ids': student_ids,
        'marks': marks,
    }

    return render(request, 'student/student_marks_report.html', context)