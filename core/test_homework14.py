from datetime import datetime, timedelta, timezone as dt_timezone

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import SubTask, Task


class Homework14Tests(APITestCase):
    def setUp(self):
        self.tuesday = Task.objects.create(title="Tuesday task", description="Tuesday",
                                          deadline=datetime(2026, 11, 10, 12, tzinfo=dt_timezone.utc))
        self.sunday = Task.objects.create(title="Sunday task", description="Sunday",
                                         deadline=datetime(2026, 11, 8, 12, tzinfo=dt_timezone.utc))
        now = timezone.now()
        for index in range(8):
            child = SubTask.objects.create(
                title=f"Child {index}", description="Child",
                task=self.tuesday if index < 6 else self.sunday,
                status=Task.Status.DONE if index % 2 else Task.Status.NEW,
                deadline=self.tuesday.deadline,
            )
            SubTask.objects.filter(pk=child.pk).update(created_at=now + timedelta(seconds=index))

    def test_weekdays_and_default_list(self):
        url = reverse("api:task-list")
        self.assertEqual(len(self.client.get(url).data["results"]), 2)
        for weekday in ("3", "tuesday", "ВТОРНИК"):
            response = self.client.get(url, {"weekday": weekday})
            self.assertEqual(response.status_code, 200)
            self.assertEqual([r["title"] for r in response.data["results"]], ["Tuesday task"])
        self.assertEqual(self.client.get(url, {"weekday": "1"}).data["results"][0]["title"], "Sunday task")
        self.assertEqual(self.client.get(url, {"weekday": "monday"}).data["results"], [])
        self.assertEqual(self.client.get(url, {"weekday": "8"}).status_code, 400)

    def test_pagination_newest_first_and_hard_limit(self):
        url = reverse("api:subtask-list-create")
        page1 = self.client.get(url).data
        self.assertEqual([r["title"] for r in page1["results"]], [f"Child {i}" for i in range(7, 1, -1)])
        self.assertIsNotNone(page1["next"])
        page2 = self.client.get(page1["next"]).data
        self.assertEqual([r["title"] for r in page2["results"]], ["Child 1", "Child 0"])
        self.assertIsNone(page2["next"])
        self.assertEqual(len(self.client.get(url, {"page_size": 100}).data["results"]), 6)
        self.assertEqual(len(self.client.get(url, {"page_size": 2}).data["results"]), 6)
        self.assertEqual(self.client.get(url, {"cursor": "a"}).status_code, 404)

    def test_filters_individually_and_together(self):
        url = reverse("api:subtask-list-create")
        self.assertEqual(len(self.client.get(url, {"task_title": "Tuesday task"}).data["results"]), 6)
        self.assertEqual(len(self.client.get(url, {"status": "done"}).data["results"]), 4)
        response = self.client.get(url, {"task_title": "Tuesday task", "status": "done"}).data
        self.assertEqual(len(response["results"]), 3)
        self.assertEqual([r["title"] for r in response["results"]], ["Child 5", "Child 3", "Child 1"])
        self.assertEqual(self.client.get(url, {"task_title": "Missing"}).data["results"], [])
        self.assertEqual(self.client.get(url, {"status": "invalid"}).status_code, 400)
        self.assertIsNotNone(self.client.get(url, {"status": "", "task_title": ""}).data["next"])
