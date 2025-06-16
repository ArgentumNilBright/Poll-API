from django.db import transaction
from django.db.models import Count
from rest_framework import serializers

from main.models import Poll, Option, Vote


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ('id', 'title',)


class PollSerializer(serializers.ModelSerializer):
    poll_options = OptionSerializer(many=True, required=True)

    class Meta:
        model = Poll
        fields = ('id', 'title', 'poll_options')

    def validate_poll_options(self, value):
        if not value:
            raise serializers.ValidationError({'poll_options': 'Нельзя создать опрос без вариантов ответа'})
        return value

    @transaction.atomic
    def create(self, validated_data):
        poll_options = validated_data.pop('poll_options')
        poll = Poll.objects.create(**validated_data)
        options = [
            Option(poll=poll, **option_data)
            for option_data in poll_options
        ]
        Option.objects.bulk_create(options)

        return poll


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ('id', 'poll', 'option', 'voter_id', 'metadata',)


class PollResultSerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ('id', 'title', 'total_votes', 'results',)

    def _get_annotated_options(self, obj):
        if not hasattr(obj, '_annotated_options'):
            obj._annotated_options = obj.poll_options.annotate(votes_count=Count('option_votes')).order_by(
                '-votes_count')

        return obj._annotated_options

    def get_results(self, obj):
        options = self._get_annotated_options(obj)

        return [
            {
                'id': option.id,
                'title': option.title,
                'votes': option.votes_count
            }
            for option in options
        ]

    def get_total_votes(self, obj):
        options = self._get_annotated_options(obj)

        return sum(option.votes_count for option in options)
