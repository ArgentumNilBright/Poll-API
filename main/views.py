from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import Poll
from main.serializers import PollSerializer, VoteSerializer, PollResultSerializer
from main.utils import get_client_ip, generate_voter_id, user_already_voted, option_does_not_exist


class PollCreateAPIView(CreateAPIView):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer


class PollListAPIView(ListAPIView):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer
    pagination_class = PageNumberPagination


class VoteAPIView(APIView):
    def get(self, request, poll_id):
        poll = get_object_or_404(Poll, id=poll_id)
        serializer = PollSerializer(instance=poll)
        return Response(serializer.data)

    def post(self, request, poll_id):
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        voter_id = request.COOKIES.get('voter_id') or generate_voter_id()

        if user_already_voted(voter_id, ip, user_agent, poll_id):
            return Response({'detail': 'Вы уже голосовали'}, status=status.HTTP_400_BAD_REQUEST)

        option_id = request.data.get('option')
        if option_does_not_exist(option_id, poll_id):
            return Response({'detail': 'Получен отсутствующий вариант ответа, или опрос с таким ID не существует'},
                            status=status.HTTP_400_BAD_REQUEST)

        vote_data = {
            'poll': poll_id,
            'option': option_id,
            'voter_id': voter_id,
            'metadata': {'ip': ip, 'user_agent': user_agent}
        }

        serializer = VoteSerializer(data=vote_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response = Response({'detail': 'Ваш голос засчитан'}, status=status.HTTP_201_CREATED)
        response.set_cookie('voter_id', voter_id, max_age=60 * 60 * 24 * 400, httponly=True)

        return response


class ResultAPIView(RetrieveAPIView):
    queryset = Poll.objects.all()
    serializer_class = PollResultSerializer
    lookup_url_kwarg = 'poll_id'
