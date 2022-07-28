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

    for k, v in valid_submissions.items():
        print(k, len(v))
    
    return valid_submissions


if __name__ == "__main__":
    course = _load_course()
    print("Retrieving submissions for ", course.name, "needing feedback...")
    valid_submissions = _get_all_valid_submissions(course)