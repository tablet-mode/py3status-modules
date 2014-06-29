#!/usr/bin/env python

"""taskstatus

Taskstatus is a taskwarrior module for py3status.
It shows the number of open tasks in your py3status bar.

Copyright (C) 2013 Tablet Mode <tablet-mode AT monochromatic DOT cc>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see [http://www.gnu.org/licenses/].

"""

from configparser import SafeConfigParser, NoSectionError
from os import path
from subprocess import check_output, CalledProcessError, STDOUT
from time import time


class TaskstatusException(Exception):

    """Custom taskstatus exception."""

    def __init__(self, exception):
        """Initialisation."""
        self.exception = exception

    def __str__(self):
        """Prepend message with 'taskstatus: '."""
        return "taskstatus: {exception}".format(exception=self.exception)


class Data:

    """Aquire data."""

    def get_tasks(self):
        """Return number of open and overdue tasks as tuple."""
        tasks = 0
        overdue = 0

        stats = check_output(["task", "stats"]).split()
        tasks = int(stats[5])

        try:
            overdueList = check_output(
                ["task", "overdue"], stderr=STDOUT).split()
            overdue = int(overdueList[len(overdueList)-2])
        except CalledProcessError as e:
            if not "No matches" in e.output:
                raise TaskstatusException("failed to execute 'task overdue'")
        except OSError:
            raise TaskstatusException("failed to execute 'task overdue'")

        return tasks, overdue


class Py3status:

    """Called by py3status."""

    def __init__(self):
        """Read config, initialise Data class."""
        # See if we can find taskwarrior.
        try:
            check_output(["task", "--version"], stderr=STDOUT)
        except OSError:
            raise TaskstatusException("failed to execute 'task'")
        self.conf = self._read_config()
        self.data = Data()

    def _read_config(self):
        """Read config file."""
        conf = {}
        config = SafeConfigParser({
            'title': 'TASK:', 'order': '0', 'interval': '0'})
        config.read([path.expanduser('~/.i3/py3status/modules.ini')])
        try:
            conf['title'] = config.get('taskstatus', 'title')
            conf['order'] = config.getint('taskstatus', 'order')
            conf['interval'] = config.getint('taskstatus', 'interval')
        except NoSectionError:
            raise TaskstatusException("no taskstatus section in config")

        return conf

    def taskstatus(self, json, i3status_config):
        """Return response for py3status."""
        TITLE = self.conf['title']
        INTERVAL = self.conf['interval']
        ORDER = self.conf['order']
        response = {'full_text': '', 'name': 'taskstatus'}

        tasks, overdue = self.data.get_tasks()

        if overdue > 0:
            response['color'] = i3status_config['color_bad']
            response['full_text'] = "%s %d/%d" % \
                (TITLE, overdue, tasks)
        else:
            response['full_text'] = "%s %d" % \
                (TITLE, tasks)

        response['cached_until'] = time() + INTERVAL

        return (ORDER, response)
