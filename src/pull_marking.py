#!/usr/bin/env python3

import json

from canvasapi import Canvas

CONFIG_FILE = "config.json"

def _load_course():
    with open("config.json") as f:
        config_data = json.load(f)

    canvas = Canvas(config_data["API_URL"], config_data["API_KEY"])
    course = canvas.get_course(config_data["COURSE_ID"])
    return course


if __name__ == "__main__":
    course = _load_course()
    print(course.name)
    