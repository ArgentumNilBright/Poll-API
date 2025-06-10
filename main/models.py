from django.db import models


class Poll(models.Model):
    title = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)


class Option(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='poll_options')
    title = models.CharField(max_length=128)


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='poll_votes')
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='option_votes')
    created_at = models.DateTimeField(auto_now_add=True)
    voter_id = models.CharField(max_length=36, null=True, blank=True)
    metadata = models.JSONField()
