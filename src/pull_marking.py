#!/usr/bin/env python3

from canvasapi import Canvas

API_URL = "https://swinburne.instructure.com/"
API_KEY = "your API key goes here"

if __name__ == "__main__":
    canvas = Canvas(API_URL, API_KEY)
    print(canvas)