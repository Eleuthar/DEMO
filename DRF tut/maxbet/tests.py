from django.test import TestCase

# Create your tests here.
from api.models import Match, Selection
from rest_framework import status
from rest_framework.test import APITestCase


class MatchTests(APITestCase):

    def test_create_match(self):
        url = ('http://127.0.0.1:8000/api/match/')
        data = {
            "id": 1,
            "message_type": "NewEvent",
            "event": {
                "id": 2,
                "name": "India vs Australia",
                "startTime": "2020-07-06 10:30:00",
                "sport": {
                    "id": 1,
                    "name": "Cricket"
                },
                "markets": [
                    {
                        "id": 1,
                        "name": "Winner",
                        "selections": [
                            {
                                "id": 2,
                                "name": "India",
                                "odds": 1.01
                            },
                            {
                                "id": 3,
                                "name": "South Africa",
                                "odds": 1.01
                            }
                        ]
                    }
                ]
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Match.objects.count(), 1)
        self.assertEqual(Match.objects.get().name, 'India vs Australia')

    def test_update_odds(self):
        url = ('http://127.0.0.1:8000/api/match/')
        create_match = {
            "id": 1,
            "message_type": "NewEvent",
            "event": {
                "id": 2,
                "name": "India vs Australia",
                "startTime": "2020-07-06 10:30:00",
                "sport": {
                    "id": 1,
                    "name": "Cricket"
                },
                "markets": [
                    {
                        "id": 1,
                        "name": "Winner",
                        "selections": [
                            {
                                "id": 2,
                                "name": "India",
                                "odds": 1.01
                            },
                            {
                                "id": 3,
                                "name": "South Africa",
                                "odds": 1.01
                            }
                        ]
                    }
                ]
            }
        }
        response = self.client.post(url, create_match, format='json')
        update_odds = {
            "id": 1,
            "message_type": "NewEvent",
            "event": {
                "id": 2,
                "name": "India vs Australia",
                "startTime": "2020-07-06 10:30:00",
                "sport": {
                    "id": 1,
                    "name": "Cricket"
                },
                "markets": [
                    {
                        "id": 1,
                        "name": "Winner",
                        "selections": [
                            {
                                "id": 2,
                                "name": "India",
                                "odds": 1.01
                            },
                            {
                                "id": 3,
                                "name": "South Africa",
                                "odds": 1.01
                            }
                        ]
                    }
                ]
            }
        }
        response = self.client.post(url, update_odds, format='json')
        self.assertEqual([1.5, 0.5], [s.odds for s in Selection.objects.all()])
        self.assertEqual(Match.objects.get().name, 'India vs Australia')
