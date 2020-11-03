def add_event(request, event):
    if 'events' not in request.session:
        request.session['events'] = {}
    request.session['events'] = {**event, **request.session['events']}


def clear(request):
    if 'events' not in request.session:
        request.session['events'] = {}
    request.session['events'] = {}


def get(request):
    if 'events' not in request.session:
        request.session['events'] = {}
    return request.session['events']
