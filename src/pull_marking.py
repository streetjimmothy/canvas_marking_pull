#!/usr/bin/env python3
import pathlib
import os
import shutil
import requests
import datetime
from canvasapi import Canvas

import utils

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def get_all_valid_submissions(course, omit_late=True, omit_graded=True):
    '''Find all valid submissions for all tasks.

    Returns a dictionary of {assignment: list of submissions}.

    For a submission to be valid it must be submitted before the task due date, and
    not have been graded yet.
    '''
    
    valid_submissions = {}
    for a in course.get_assignments():
        print("- pulling submissions for", a.name)

        valid_submissions[a] = []
        for s in a.get_submissions():
            if s.submitted_at is not None: # something was submitted
                if s.late and not omit_late:
                    if (s.graded_at is None or s.graded_at_date < s.submitted_at_date) and not omit_graded:
                        valid_submissions[a].append(s)

    return valid_submissions


def find_lab(course, student_user_id):
    '''Get string representation for the lab a specific student in a course is enrolled in.'''

    course_enrollments = [e for e in course.get_enrollments(user_id=student_user_id)]
    for en in course_enrollments:
        section = course.get_section(en.course_section_id)
        if "Class" in section.name:
            return section.name

    return "No lab"

students = {}
def getStudentDetails(course, student_user_id):
    if not students.get(student_user_id):
        user = course.get_user(student_user_id)
        students[student_user_id] = user
    return students[student_user_id]


def generate_csv(course, valid_submissions, target_dir):
    '''Generate a csv called "marking.csv containing a summary of tasks that need feedback,
    and links to the speedgrader to show each task.
    '''

    print("Generating csv...")
    student_details = {} # cache student details to avoid unnecessary requests; {userid: ("name, student_id, lab")}

    with open(pathlib.PurePath(target_dir).joinpath("marking.csv"), "w+") as f:
        f.write("Task, Student, Student ID, Lab, Submitted on, Submission number, Link\n")
        for assignment, submissions in valid_submissions.items():
            print("- adding entries for", assignment.name)
            for s in submissions:
                student_string = student_details.get(s.user_id)
                if not student_string:
                    user = course.get_user(s.user_id)
                    student_string = user.name + "," + str(user.login_id) + "," + find_lab(course, s.user_id)
                    student_details[s.user_id] = student_string
                f.write('"' + assignment.name + '",'
                    + student_string + ","
                    + s.submitted_at_date.strftime("%d %B") + ","
                    + str(s.attempt) + ","
                    + utils.speedgrader_link(course, assignment, s)
                    + "\n")

def checkDHDprereqs(course):
    '''Check if students have completed the DHD prerequisites.'''

    print("Checking DHD prerequisites...")
    dhd = course.get_assignment(587257)
    dhd_submissions = dhd.get_submissions()
    for s in dhd_submissions:
        if s.submitted_at is not None:
            #get the user for the assignment
            user = course.get_user(s.user_id)
            #get all their other assignments
            assignments = course.get_assignments()
            #check if they have submitted the prerequisites
            prereq_met = True
            for a in assignments:
                #get the first two chracters of the assignment name
                a_number = a.name[:2]
                #convert to a number
                a_number = int(a_number)
                #check the number is less that the threshold
                if a_number < 17:
                #check if the assignment has been submitted
                    if a.get_submission(s.user_id).submitted_at is None:
                        prereq_met = False
                        break
            if prereq_met:
                print(user.name, "has completed the prerequisites for DHD.")
            else:
                print(user.name, "has not completed the prerequisites for DHD.")

def dump_portfolios(course, target_dir):
    '''Dump the portfolios of all students in the course.'''

    print("Dumping portfolios...")

    user_portfolios = {}
    for a in course.get_assignments():
        print("- pulling submissions for", a.name)
        for s in a.get_submissions():
            if s.submitted_at is not None:
                s.assignment_name = a.name
                if s.user_id not in user_portfolios:
                    user_portfolios[s.user_id] = [s]
                else:
                    user_portfolios[s.user_id].append(s)
    
    for user_id, submissions in user_portfolios.items():
        student = course.get_user(user_id)
        if len(submissions) < 15:
            print(f"{bcolors.BOLD}{bcolors.FAIL}Portfolio for {student.login_id}, {student.name} is incomplete. FAIL")
        else:
            print(f"Dumping portfolio for {student.login_id}, {student.name}")
            path = pathlib.PurePath(target_dir).joinpath(f"{student.login_id}, {student.name}")
            if os.path.exists(path):
                shutil.rmtree(path)
            os.mkdir(path)
            for s in submissions:
                for a in s.attachments:
                    try:
                        response = requests.get(a.url)
                        response.raise_for_status()
                        with open(path.joinpath(path, f"{s.assignment_name} - {a.filename}"), "wb") as f:
                            f.write(response.content)
                    except:
                        print(f"{bcolors.FAIL}Failed to download {a.filename} for {student.login_id}, {student.name}")

def setUnsumbittedandLatetoZero(course):
    '''Set the unsubmitted and late assignments to zero.'''
    print("Setting unsubmitted and late assignments to zero...")
    for a in course.get_assignments():
        print("- setting grades for", a.name)
        for s in a.get_submissions():
            if s.submitted_at is None and s.cached_due_date_date.timestamp() < datetime.datetime.now().timestamp():
                print(f"Setting {getStudentDetails(course, s.user_id).name}'s grade for {a.name} to 0.")
                s.edit(submission={'posted_grade': 0})

def setFailGrades(course):
    print("Setting Fail Grades...")
    submissions_required = 20

    manual_review = []
    user_portfolios = {}
    for a in course.get_assignments():
        print("- pulling submissions for", a.name)
        for s in a.get_submissions():
            if s.submitted_at is not None:
                s.assignment_name = a.name
                if s.user_id not in user_portfolios:
                    user_portfolios[s.user_id] = [s]
                else:
                    user_portfolios[s.user_id].append(s)
    LSR = course.get_assignment(631990)

    for user_id, submissions in user_portfolios.items():
        student = getStudentDetails(course, user_id)
        num_submissions = len(submissions)
        if num_submissions < submissions_required:
            print(f"{bcolors.BOLD}{bcolors.FAIL}Portfolio for {student.login_id}, {student.name} is incomplete. FAIL")
            if num_submissions < submissions_required-10:
                print(f"{student.name} has {num_submissions} submissions. Setting {student.name}'s grade for {a.name} to 0.")
                LSR.edit(submission={'posted_grade': 0})
            elif num_submissions < submissions_required-8:
                print(f"{student.name} has {num_submissions} submissions. Setting {student.name}'s grade for {a.name} to 15.")
                LSR.edit(submission={'posted_grade': 15})
            elif num_submissions < submissions_required-6:
                print(f"{student.name} has {num_submissions} submissions. Setting {student.name}'s grade for {a.name} to 25.")
                LSR.edit(submission={'posted_grade': 25})
            elif num_submissions < submissions_required-4:
                print(f"{student.name} has {num_submissions} submissions. Setting {student.name}'s grade for {a.name} to 35.")
                LSR.edit(submission={'posted_grade': 35})
            elif num_submissions < submissions_required-3:
                print(f"{student.name} has {num_submissions} submissions. Setting {student.name}'s grade for {a.name} to 40.")
                LSR.edit(submission={'posted_grade': 40})
            elif num_submissions < submissions_required-2:
                print(f"{student.name} has {num_submissions} submissions. Setting {student.name}'s grade for {a.name} to 40.")
                LSR.edit(submission={'posted_grade': 45})
            elif num_submissions < submissions_required-1:
                print(f"{student.name} has {num_submissions} submissions. Needs manual review.")
                manual_review.append(student.name)
            
            
    print("Manual Review Required:")
    for student in manual_review:
        print(student)

if __name__ == "__main__":
    target_dir = "C:\\Users\\jabcm\\OneDrive - Swinburne University\\AI4G\\Portfolios"
    course = utils.load_course()
    #setUnsumbittedandLatetoZero(course)
    setFailGrades(course)
    #print("Retrieving submissions for", course.name, "needing feedback...")
    #valid_submissions = get_all_valid_submissions(course, False, False)
    #generate_csv(course, valid_submissions, target_dir)
    #checkDHDprereqs(course)
    dump_portfolios(course, target_dir)
