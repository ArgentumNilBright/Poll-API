import uuid

from django.test import TestCase

from main.models import Poll, Option, Vote
from main.serializers import PollSerializer, OptionSerializer, VoteSerializer, PollResultSerializer


class OptionSerializerTest(TestCase):
    def test_option_serializer_output(self):
        poll = Poll.objects.create(title="Test Poll")
        option = Option.objects.create(title="Option 1", poll=poll)

        serializer = OptionSerializer(instance=option)
        data = serializer.data

        self.assertEqual(data['title'], "Option 1")
        self.assertIn('id', data)


class PollSerializerTest(TestCase):
    def test_poll_serializer_fails_without_title(self):
        data = {
            "poll_options": [{"title": "Option 1"}]
        }

        serializer = PollSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_poll_serializer_fails_without_options(self):
        data = {
            "title": "Incomplete Poll"
        }

        serializer = PollSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('poll_options', serializer.errors)

    def test_poll_serializer_fails_with_empty_options(self):
        data = {
            "title": "Empty Options Poll",
            "poll_options": []
        }

        serializer = PollSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('poll_options', serializer.errors)


class VoteSerializerTest(TestCase):
    def setUp(self):
        self.poll = Poll.objects.create(title="Vote Test Poll")
        self.option = Option.objects.create(title="Valid Option", poll=self.poll)

    def test_vote_serializer_fails_without_poll(self):
        data = {
            "option": str(self.option.id),
            "voter_id": str(uuid.uuid4()),
            "metadata": {"ip": "127.0.0.1", "user_agent": "TestAgent"}
        }

        serializer = VoteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('poll', serializer.errors)

    def test_vote_serializer_fails_with_invalid_option(self):
        data = {
            "poll": str(self.poll.id),
            "option": "invalid-uuid",
            "voter_id": str(uuid.uuid4()),
            "metadata": {"ip": "127.0.0.1", "user_agent": "TestAgent"}
        }

        serializer = VoteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('option', serializer.errors)

    def test_vote_serializer_fails_without_metadata(self):
        data = {
            "poll": str(self.poll.id),
            "option": str(self.option.id),
            "voter_id": str(uuid.uuid4())
        }

        serializer = VoteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('metadata', serializer.errors)


class PollResultSerializerTest(TestCase):
    def test_poll_result_serializer_counts_votes_correctly(self):
        poll = Poll.objects.create(title="Poll with Results")
        option1 = Option.objects.create(poll=poll, title="Option 1")
        option2 = Option.objects.create(poll=poll, title="Option 2")

        Vote.objects.create(poll=poll, option=option1, voter_id=str(uuid.uuid4()), metadata={})
        Vote.objects.create(poll=poll, option=option1, voter_id=str(uuid.uuid4()), metadata={})
        Vote.objects.create(poll=poll, option=option2, voter_id=str(uuid.uuid4()), metadata={})

        serializer = PollResultSerializer(instance=poll)
        data = serializer.data

        self.assertEqual(data['total_votes'], 3)
        self.assertEqual(len(data['results']), 2)

        self.assertEqual(data['results'][0]['title'], "Option 1")
        self.assertEqual(data['results'][0]['votes'], 2)
        self.assertEqual(data['results'][1]['votes'], 1)
