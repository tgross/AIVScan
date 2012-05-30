from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

import simplejson

from aivs import tasks

'''
This module contains the main logic of the web application.  Although the module is called views
in the Django convention, this module takes the role of Controller in the classic MVC pattern.
'''

@login_required
def request_scan(request):
    if request.method == 'POST':
        # we bind a form to the POST data
        form = ScanRequestForm(request.POST)
        if form.is_valid():
            # form.cleaned_data now contains only valid data
            user = request.user
            ip = get_client_ip(request)
            tasks.run_scan.delay(user, ip)
            return HttpResponseRedirect('/success/')
    else:
        # form has not been submitted, so prepare an unbound form
        form = ScanRequestForm()
    return render_to_response('submit_scan_form.html', {'form': form})

'''
TODO: Ajaxify the above
def scan(request):
    form = ScanRequestForm(request.POST)
    if form.is_valid():
        form.save()
        d = {'error': 0, 'message': 'success'}
    else:
        d = {'error': 1}
        form_html = render_to_string('submit_scan_form.html',
                                     context_instance=RequestContext(request))
        d['message'] = form_html
    response = simplejson.dumps(d)
    return HttpResponse(response, mimetype='application/json')
'''

def get_client_ip(request):
    '''
    Gets the client IP address from the request headers, including handling proxies.
    TODO: this is where we should validate format of the IP address.
    '''
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
