#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/home/bitnami/blog")
 
from blog import app as application
application.secret_key = "TODO: Get this from a file outside what's available on the server"