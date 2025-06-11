from django.urls import path

from main.views import PollCreateAPIView, PollListAPIView, VoteAPIView, ResultAPIView

urlpatterns = [
    path('api/v1/createpoll/', PollCreateAPIView.as_view(), name='poll_create'),
    path('api/v1/polls/', PollListAPIView.as_view(), name='poll_list'),
    path('api/v1/polls/<uuid:poll_id>/', VoteAPIView.as_view(), name='poll_vote'),
    path('api/v1/getresult/<uuid:poll_id>/', ResultAPIView.as_view(), name='poll_result'),
]