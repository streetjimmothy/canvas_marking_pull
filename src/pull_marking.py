#!/usr/bin/env python3

from canvasapi import Canvas

import utils

def get_all_valid_submissions(course):
    '''Find all valid submissions for all tasks.

    Returns a dictionary of {assignment: list of submissions}.

    For a submission to be valid it must be submitted before the task due date, and
    not have been graded yet.
    '''
    
    valid_submissions = {}
    for a in course.get_assignments():
        print("- pulling submissions for", a.name)
        submissions = [s for s in a.get_submissions() 
            if s.submitted_at is not None # something was submitted
            and s.submitted_at_date <= a.due_at_date # it's not overdue
            and (s.graded_at is None or s.graded_at_date < s.submitted_at_date)] # it hasn't ever been graded, or the grade there is for an older submission
        if len(submissions) > 0:
            valid_submissions[a] = submissions
    
    return valid_submissions


def find_lab(course, student_user_id):
    '''Get string representation for the lab a specific student in a course is enrolled in.'''

    course_enrollments = [e for e in course.get_enrollments(user_id=student_user_id)]
    for en in course_enrollments:
        section = course.get_section(en.course_section_id)
        if "Class" in section.name:
            return section.name

    return "No lab"


def generate_csv(course, valid_submissions):
    '''Generate a csv called "marking.csv containing a summary of tasks that need feedback,
    and links to the speedgrader to show each task.
    '''

    print("Generating csv...")
    student_details = {} # cache student details to avoid unnecessary requests; {userid: ("name, student_id, lab")}

    with open("marking.csv", "w+") as f:
        f.write("Task, Student, Student ID, Lab, Submitted on, Submission number, Link\n")
        for assignment, submissions in valid_submissions.items():
            print("- adding entries for", assignment.name)
            for s in submissions:
                student_string = student_details.get(s.user_id)
                if not student_string:
                    user = course.get_user(s.user_id)
                    student_string = user.name + "," + str(user.login_id) + "," + find_lab(course, s.user_id)
                    student_details[s.user_id] = student_string
                f.write(assignment.name + ","
                    + student_string + ","
                    + s.submitted_at_date.strftime("%d %B") + ","
                    + str(s.attempt) + ","
                    + utils.speedgrader_link(course, assignment, s)
                    + "\n")


if __name__ == "__main__":
    course = utils.load_course()
    print("Retrieving submissions for", course.name, "needing feedback...")
    valid_submissions = get_all_valid_submissions(course)
    generate_csv(course, valid_submissions)
