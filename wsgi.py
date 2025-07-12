#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WSGI entry point for Sistema Espetinho
Para uso em produção com Gunicorn, uWSGI, etc.
"""

from app import app

if __name__ == "__main__":
    app.run() 