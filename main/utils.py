import uuid

from main.models import Vote, Option


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_voter_id():
    return str(uuid.uuid4())


def user_already_voted(voter_id, ip, user_agent, poll_id):
    queryset = Vote.objects.filter(poll=poll_id)
    if voter_id:
        already_voted = queryset.filter(voter_id=voter_id).exists()
    else:
        already_voted = queryset.filter(metadata__ip=ip, metadata__user_agent=user_agent).exists()

    return already_voted


def option_does_not_belong_to_poll(option_id, poll_id):
    queryset = Option.objects.filter(poll_id=poll_id)
    option_does_not_exist = not queryset.filter(id=option_id).exists()

    return option_does_not_exist
