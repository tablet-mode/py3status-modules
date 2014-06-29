#!/usr/bin/env python

"""mailstatus

Mailstatus is an email module for py3status.
It shows the number of unread mails in your mailboxes.

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

from configparser import SafeConfigParser, NoOptionError, NoSectionError
from mailbox import Maildir, NoSuchMailboxError
from os import listdir, path
from shlex import split
from time import time


class MailstatusException(Exception):

    """Custom mailstatus exception."""

    def __init__(self, exception):
        """Initialisation."""
        self.exception = exception

    def __str__(self):
        """Prepend message with 'mailstatus: '."""
        return "mailstatus: {exception}".format(exception=self.exception)


class Data:

    """Aquire data."""

    def __init__(self, mailboxes):
        """Initialise data."""
        self.read_mailboxes(mailboxes)

    def read_mailboxes(self, mailboxes):
        """Return list of mailboxes.

        Raise exception on invalid mailbox.

        """
        mboxes = []
        state = []
        unread = []
        if mailboxes:
            for mdir in mailboxes:
                try:
                    mbox = Maildir(mdir, create=False)
                    mbox.keys()
                    mboxes.append(mbox)
                    state.append('')
                    unread.append(0)
                except NoSuchMailboxError:
                    raise MailstatusException(
                        "invalid path: {path}".format(path=mdir))
                except FileNotFoundError:
                    raise MailstatusException(
                        "invalid maildir: {path}".format(path=mdir))
        self.mboxes = mboxes
        self.mbox_state = state
        self.unread = unread

    def get_unread_maildir(self, mbox):
        """Shortcut for maildir format.

        Get number of unread mails by simply counting the number of files in
        the 'new' folder.

        """
        mdir = mbox._paths['new']
        unread = len(
            [item for item in listdir(mdir) if path.isfile(path.join(
                mdir, item))])
        return unread

    def get_unread(self):
        """Return number of unread emails."""
        unread_mails = 0
        if not self.mboxes:
            unread_mails = 'no mailbox configured'
            return unread_mails

        last_state = self.mbox_state[:]
        unread_per_box = self.unread[:]
        ct = 0
        for mbox in self.mboxes:
            mbox.keys()
            self.mbox_state[ct] = mbox._toc
            if self.mbox_state[ct] == last_state[ct]:
                pass
            else:
                unread_per_box[ct] = 0
                if isinstance(mbox, Maildir):
                    unread_per_box[ct] = self.get_unread_maildir(mbox)
                else:
                    for message in mbox:
                        flags = message.get_flags()
                        if 'S' not in flags:
                            unread_per_box[ct] += 1
            ct += 1
        for mail in unread_per_box:
            unread_mails += mail
        self.unread = unread_per_box

        return unread_mails


class Py3status:

    """This is where all the py3status magic happens."""

    def __init__(self):
        """Read config and initialise Data class."""
        self.conf = self._read_config()
        self.data = Data(self.conf['mailboxes'])
        self.status = 'unread'

    def _read_config(self):
        """Read config file."""
        conf = {}
        config = SafeConfigParser({
            'title': 'MAIL:', 'order': '0', 'interval': '0'})
        config.read([path.expanduser('~/.i3/py3status/modules.ini')])

        try:
            conf['mailboxes'] = split(config.get('mailstatus', 'mailboxes'))
            conf['title'] = config.get('mailstatus', 'title')
            conf['order'] = config.getint('mailstatus', 'order')
            conf['interval'] = config.getint('mailstatus', 'interval')
        except NoSectionError:
            raise MailstatusException("no mailstatus section in config")
        except NoOptionError:
            raise MailstatusException("no mailboxes configured")

        return conf

    def mailstatus(self, json, i3status_config):
        """Return response for i3status bar."""
        title = self.conf['title']
        interval = self.conf['interval']
        order = self.conf['order']
        response = {'full_text': '', 'name': 'mailstatus'}
        unread = self.data.get_unread()

        if isinstance(unread, str):
            response['color'] = i3status_config['color_bad']
            response['full_text'] = "%s %s" % (
                title, unread)
        else:
            if unread > 0:
                response['color'] = i3status_config['color_degraded']
            response['full_text'] = "%s %d" % (
                title, unread)

        response['cached_until'] = time() + interval

        return (order, response)
