#!/usr/bin/env python3

import json
import os

from canvasapi import Canvas

CONFIG_FILE = "config.json"

def _load_course():
    '''Load the configuration from file and create a session connecting to the relevant course.

    Returns the course object.
    '''

    # load config
    with open("config.json") as f:
        config_data = json.load(f)
    api_key = config_data["API_KEY"]

    # use environment variable api key if present -- takes precedent over config file
    try:
        api_key = os.environ["CANVAS_KEY"]
    except:
        pass

    # connect to canvas and retrieve course
    canvas = Canvas(config_data["API_URL"], api_key)
    course = canvas.get_course(config_data["COURSE_ID"])
    return course


def _get_all_valid_submissions(course):
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
        valid_submissions[a] = submissions
    
    return valid_submissions


def __speedgrader_link(course, assignment, submission):
    '''Get a speedgrader formatted link for viewing a specific submission on an assignment.'''

    return "https://swinburne.instructure.com/courses/" + str(course.id) + "/gradebook/speed_grader?assignment_id=" + str(assignment.id) + "&student_id=" + str(submission.user_id)


def __find_lab(course, student_user_id):
    course_enrollments = [e for e in course.get_enrollments(user_id=student_user_id)]
    for en in course_enrollments:
        section = course.get_section(en.course_section_id)
        if "Lab" in section.name:
            return section.name

    return "No lab"


def _generate_csv(course, valid_submissions):
    '''Generate a csv called "marking.csv containing a summary of tasks that need feedback,
    and links to the speedgrader to show each task.
    '''

    student_details = {} # cache student details to avoid unnecessary requests; {userid: ("name, student_id, lab")}

    with open("marking.csv", "w+") as f:
        f.write("Task, Student, Student ID, Lab, Submitted on, Times assessed, Link\n")
        for assignment, submissions in valid_submissions.items():
            for s in submissions:
                student_string = student_details.get(s.user_id)
                if not student_string:
                    user = course.get_user(s.user_id)
                    student_string = user.name + "," + str(user.login_id) + "," + __find_lab(course, s.user_id)
                    student_details[s.user_id] = student_string

                f.write(assignment.name + ","
                    + student_string + ","
                    + s.submitted_at_date.strftime("%d %B") + ","
                    + str(s.attempt) + ","
                    + __speedgrader_link(course, assignment, s)
                    + "\n")


if __name__ == "__main__":
    course = _load_course()
    print("Retrieving submissions for ", course.name, "needing feedback...")
    valid_submissions = _get_all_valid_submissions(course)
    _generate_csv(course, valid_submissions)