"""
sentry.plugins.sentry_mail.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import sentry

from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from sentry.conf import settings
from sentry.plugins import register
from sentry.plugins.bases.notify import NotificationPlugin
from sentry.utils.http import absolute_uri

from pynliner import Pynliner

NOTSET = object()


class UnicodeSafePynliner(Pynliner):
    def _get_output(self):
        """
        Generate Unicode string of `self.soup` and set it to `self.output`

        Returns self.output
        """
        self.output = unicode(self.soup)
        return self.output


class MailPlugin(NotificationPlugin):
    title = _('Mail')
    conf_key = 'mail'
    slug = 'mail'
    version = sentry.VERSION
    author = "Sentry Team"
    author_url = "https://github.com/getsentry/sentry"
    project_default_enabled = True
    project_conf_form = None
    can_disable = False
    subject_prefix = settings.EMAIL_SUBJECT_PREFIX

    def _send_mail(self, subject, body, html_body=None, project=None, fail_silently=False, headers=None):
        send_to = self.get_send_to(project)
        if not send_to:
            return

        subject_prefix = self.get_option('subject_prefix', project) or self.subject_prefix

        msg = EmailMultiAlternatives(
            '%s%s' % (subject_prefix, subject),
            body,
            settings.SERVER_EMAIL,
            send_to,
            headers=headers)
        if html_body:
            msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=fail_silently)

    def send_test_mail(self, project=None):
        self._send_mail(
            subject='Test Email',
            body='This email was requested as a test of Sentry\'s outgoing email',
            project=project,
            fail_silently=False,
        )

    def get_notification_settings_url(self):
        return absolute_uri(reverse('sentry-account-settings-notifications'))

    def on_alert(self, alert):
        project = alert.project
        subject = '[{0}] ALERT: {1}'.format(
            project.name.encode('utf-8'),
            alert.message.encode('utf-8'),
        )
        body = self.get_alert_plaintext_body(alert)
        html_body = self.get_alert_html_body(alert)

        headers = {
            'X-Sentry-Project': project.name,
        }

        self._send_mail(
            subject=subject,
            body=body,
            html_body=html_body,
            project=project,
            fail_silently=False,
            headers=headers,
        )

    def get_alert_plaintext_body(self, alert):
        return render_to_string('sentry/emails/alert.txt', {
            'alert': alert,
            'link': alert.get_absolute_url(),
        })

    def get_alert_html_body(self, alert):
        return UnicodeSafePynliner().from_string(render_to_string('sentry/emails/alert.html', {
            'alert': alert,
            'link': alert.get_absolute_url(),
            'settings_link': self.get_notification_settings_url(),
        })).run()

    def notify_users(self, group, event, fail_silently=False):
        project = group.project

        interface_list = []
        for interface in event.interfaces.itervalues():
            body = interface.to_string(event)
            if not body:
                continue
            interface_list.append((interface.get_title(), body))

        subject = '[%s] %s: %s' % (
            project.name.encode('utf-8'),
            unicode(event.get_level_display()).upper().encode('utf-8'),
            event.error().encode('utf-8').splitlines()[0])

        link = group.get_absolute_url()

        body = self.get_plaintext_body(group, event, link, interface_list)

        html_body = self.get_html_body(group, event, link, interface_list)

        headers = {
            'X-Sentry-Logger': event.logger,
            'X-Sentry-Logger-Level': event.get_level_display(),
            'X-Sentry-Project': project.name,
            'X-Sentry-Server': event.server_name,
        }

        self._send_mail(
            subject=subject,
            body=body,
            html_body=html_body,
            project=project,
            fail_silently=fail_silently,
            headers=headers,
        )

    def get_plaintext_body(self, group, event, link, interface_list):
        return render_to_string('sentry/emails/error.txt', {
            'group': group,
            'event': event,
            'link': link,
            'interfaces': interface_list,
        })

    def get_html_body(self, group, event, link, interface_list):
        return UnicodeSafePynliner().from_string(render_to_string('sentry/emails/error.html', {
            'group': group,
            'event': event,
            'link': link,
            'interfaces': interface_list,
            'settings_link': self.get_notification_settings_url(),
        })).run()


# Legacy compatibility
MailProcessor = MailPlugin

register(MailPlugin)
