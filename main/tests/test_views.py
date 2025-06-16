import json
import uuid

from django.test import TestCase, Client
from django.urls import reverse

from main.models import Poll, Option, Vote


class PollAPIViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.poll = Poll.objects.create(title="Test Poll")
        self.option = Option.objects.create(poll=self.poll, title="Option 1")

    def test_poll_create_view(self):
        url = reverse('poll_create')
        data = {
            "title": "New Poll",
            "poll_options": [
                {"title": "Option 1"},
                {"title": "Option 2"}
            ]
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Poll.objects.count(), 2)
        self.assertEqual(Option.objects.count(), 3)

    def test_poll_create_view_with_empty_options(self):
        url = reverse('poll_create')
        data = {
            "title": "New Poll",
            "poll_options": [],
        }
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Poll.objects.count(), 1)
        self.assertEqual(Option.objects.count(), 1)

    def test_poll_list_view(self):
        url = reverse('poll_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.json())
        self.assertIn("poll_options", response.json()["results"][0])
        self.assertEqual(response.json()["count"], 1)


class VoteAPIViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.poll = Poll.objects.create(title="Vote Poll")
        self.option = Option.objects.create(poll=self.poll, title="Option 1")
        self.url = reverse('poll_vote', kwargs={"poll_id": self.poll.id})
        self.invalid_poll_url = reverse('poll_vote', kwargs={"poll_id": uuid.uuid4()})
        self.headers = {
            'HTTP_USER_AGENT': 'TestAgent',
            'REMOTE_ADDR': '127.0.0.1',
        }

    def test_get_existing_poll(self):
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], self.poll.title)

    def test_get_nonexistent_poll(self):
        response = self.client.get(self.invalid_poll_url, **self.headers)
        self.assertEqual(response.status_code, 404)

    def test_post_vote_successfully(self):
        data = {"option": str(self.option.id)}
        response = self.client.post(self.url, data=json.dumps(data),
                                    content_type='application/json',
                                    **self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['detail'], "Ваш голос засчитан")
        self.assertEqual(Vote.objects.count(), 1)

        vote = Vote.objects.first()
        self.assertEqual(str(vote.option.id), data['option'])
        self.assertIn('ip', vote.metadata)
        self.assertIn('user_agent', vote.metadata)
        self.assertIn('voter_id', response.cookies)

    def test_post_vote_with_invalid_option(self):
        data = {"option": str(uuid.uuid4())}
        response = self.client.post(self.url, data=json.dumps(data),
                                    content_type='application/json',
                                    **self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("отсутствующий вариант", response.json()['detail'])

    def test_post_vote_already_voted(self):
        voter_id = str(uuid.uuid4())
        self.client.cookies['voter_id'] = voter_id
        Vote.objects.create(
            poll=self.poll,
            option=self.option,
            voter_id=voter_id,
            metadata={"ip": "127.0.0.1", "user_agent": "TestAgent"}
        )

        data = {"option": str(self.option.id)}
        response = self.client.post(self.url, data=json.dumps(data),
                                    content_type='application/json',
                                    **self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail'], "Вы уже голосовали")


class ResultAPIViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.poll = Poll.objects.create(title="Result Poll")
        self.option1 = Option.objects.create(poll=self.poll, title="Option 1")
        self.option2 = Option.objects.create(poll=self.poll, title="Option 2")
        Vote.objects.create(poll=self.poll, option=self.option1, voter_id=str(uuid.uuid4()), metadata={})
        Vote.objects.create(poll=self.poll, option=self.option1, voter_id=str(uuid.uuid4()), metadata={})
        Vote.objects.create(poll=self.poll, option=self.option2, voter_id=str(uuid.uuid4()), metadata={})

    def test_poll_result_view(self):
        url = reverse('poll_result', kwargs={"poll_id": self.poll.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], self.poll.title)
        self.assertEqual(data['total_votes'], 3)
        self.assertEqual(len(data['results']), 2)
