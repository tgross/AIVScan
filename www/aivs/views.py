from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

import re
import simplejson

from aivs.forms import ContactForm, ScanRequestForm
from scanner import tasks
from scanner.models import *
'''
This module contains the main logic of the web application.  Although the module is called views
in the Django convention, this module takes the role of Controller in the classic MVC pattern.
'''

@login_required(login_url='/login/')
def request_scan(request):
    ip = get_client_ip(request)
    if not ip:
        return HttpResponseForbidden # invalid client IP address sent

    if request.method == 'POST':
        # we bind a form to the POST data
        form = ScanRequestForm(request.POST)
        if form.is_valid():
            # form.cleaned_data now contains only valid data
            user = request.user
            tasks.run_scan.delay(user, ip)
            return HttpResponseRedirect('/profile/') # <- this should redirect to success page
    else:
        # form has not been submitted, so prepare an unbound form
        form = ScanRequestForm()
    return render_to_response('scan.html', {'form': form, 'ip': ip},
                              context_instance=RequestContext(request))


@login_required(login_url='/login/')
def profile(request):
    user = request.user
    scans = list(Scans.objects.filter(userid=user).order_by('-endtime'))
    for scan in scans:
        host = Hosts.objects.get(sid=scan.sid)
        scan.ip = host.ip4
        scan.hostname = host.hostname
    return render_to_response('profile.html', {'user':user, 'scans': scans},
                              context_instance=RequestContext(request))


@login_required(login_url='/login/')
def scan_report(request, id):
    '''
    Queries for a scan and its related objects.
    '''
    user = request.user
    try:
        report = Scans.objects.get(pk=id, userid=user.id)
        host = Hosts.objects.get(sid=report.sid)
        try:
            OS = Os.objects.get(hid=host.hid)
        except:
            OS = MockModel()
            OS.name = 'No OS information detected.'
        ports = Ports.objects.filter(hid=host.hid)
        vulns = Textvulns.objects.filter(vulns__hid=host.hid)

        return render_to_response('report.html',
                                  {'user':user,
                                   'report':report,
                                   'host':host,
                                   'OS':OS,
                                   'ports':ports,
                                   'vulns':vulns,
                                   },
                                  context_instance=RequestContext(request))
    except Scans.DoesNotExist:
        pass # TODO: do some kind of proper error handling here

def contact(request):
    if request.method == 'POST':
        # bind a form to the POST data
        form = ContactForm(request.POST)
        if form.is_valid():
            # form.cleaned_data now contains only valid data
            user_email = form.cleaned_data['email_address']
            message = form.cleaned_data['message']
            tasks.send_admin_email(user_email, message)
            return HttpResponseRedirect('/')
    else:
        # the form has not been submitted, so prepare an unbound form
        form = ContactForm()
    return render_to_response('contact.html', {'form': form},
                              context_instance=RequestContext(request))


ip_regex_pattern = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')

def get_client_ip(request):
    '''
    Gets the client IP address from the request header set by the Nginx proxy, and performs some
    simple validation.  If the check fails in a debug environment (ex. local development without
    Nginx proxy), fill in the local IP.
    In a production environment, we might not want to use this header by itself, as load balancers
    might show up as the IP.
    '''
    ip = request.META.get('HTTP_X_REAL_IP', None)
    if ip and ip_regex_pattern.match(ip):
        return ip
    elif settings.DEBUG:
        return 'localhost'
    else:
        return None


