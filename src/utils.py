import json
import os

from canvasapi import Canvas

CONFIG_FILE = "config.json"

def load_course():
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


def speedgrader_link(course, assignment, submission):
    '''Get a speedgrader formatted link for viewing a specific submission on an assignment.'''

    return "https://swinburne.instructure.com/courses/" + str(course.id) + "/gradebook/speed_grader?assignment_id=" + str(assignment.id) + "&student_id=" + str(submission.user_id)
