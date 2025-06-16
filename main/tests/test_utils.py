import uuid
from unittest import TestCase

from django.test import RequestFactory

from main.models import Poll, Option, Vote
from main.utils import generate_voter_id, user_already_voted, option_does_not_exist, get_client_ip


class UtilsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.poll = Poll.objects.create(title="Test Poll")
        self.option = Option.objects.create(poll=self.poll, title="Option 1")

    def test_generate_voter_id_returns_valid_uuid(self):
        voter_id = generate_voter_id()
        try:
            uuid_obj = uuid.UUID(voter_id, version=4)
        except ValueError:
            self.fail("generate_voter_id did not return a valid UUIDv4")

        self.assertEqual(str(uuid_obj), voter_id)

    def test_user_already_voted_with_voter_id_true(self):
        voter_id = uuid.uuid4()
        Vote.objects.create(poll=self.poll, option=self.option, voter_id=voter_id, metadata={})
        self.assertTrue(
            user_already_voted(voter_id=voter_id, ip="192.168.0.1", user_agent="TestAgent", poll_id=self.poll.id))

    def test_user_already_voted_with_ip_and_user_agent_true(self):
        Vote.objects.create(
            poll=self.poll,
            option=self.option,
            voter_id=None,
            metadata={"ip": "192.168.0.1", "user_agent": "TestAgent"}
        )
        self.assertTrue(
            user_already_voted(voter_id=None, ip="192.168.0.1", user_agent="TestAgent", poll_id=self.poll.id))

    def test_user_already_voted_returns_false_if_no_vote(self):
        self.assertFalse(
            user_already_voted(voter_id=uuid.uuid4(), ip="192.168.0.1", user_agent="TestAgent", poll_id=self.poll.id))

    def test_option_does_not_exist_returns_false_for_existing_option(self):
        self.assertFalse(option_does_not_exist(option_id=self.option.id, poll_id=self.poll.id))

    def test_option_does_not_exist_returns_true_for_invalid_option(self):
        self.assertTrue(option_does_not_exist(option_id=uuid.uuid4(), poll_id=self.poll.id))

    def test_get_client_ip_returns_correct_ip(self):
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.0.1'
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.0.1')

    def test_get_client_ip_accounts_for_x_forwarded_for(self):
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.0.1, 192.168.0.255'
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.0.1')
