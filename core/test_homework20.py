from secrets import token_urlsafe

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase


class RegistrationAndCookieAuthTests(APITestCase):
    def test_registration_validates_fields_and_hashes_password(self):
        url = reverse("api:register")
        self.assertEqual(self.client.post(url, {}).status_code, 400)
        self.assertEqual(self.client.post(url, {
            "username": "alice", "email": "invalid", "password": "123",
        }).status_code, 400)
        self.assertEqual(self.client.post(url, {
            "username": "alice", "email": "alice@example.com", "password": "123",
        }).status_code, 400)

        payload = {"username": "alice", "email": "Alice@example.com", "password": token_urlsafe()}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)
        user = get_user_model().objects.get(username="alice")
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotEqual(user.password, payload["password"])
        self.assertEqual(self.client.post(url, {**payload, "email": "other@example.com"}).status_code, 400)
        self.assertEqual(self.client.post(url, {**payload, "username": "bob"}).status_code, 400)

    def test_cookie_login_csrf_refresh_rotation_and_logout(self):
        client = APIClient(enforce_csrf_checks=True, HTTP_ORIGIN="https://testserver")
        password = token_urlsafe()
        get_user_model().objects.create_user(username="alice", password=password)
        login = reverse("api:auth-login")
        credentials = {"username": "alice", "password": password}
        self.assertEqual(client.post(login, credentials, secure=True).status_code, 403)
        csrf = client.get(reverse("api:auth-csrf"), secure=True).data["csrfToken"]
        response = client.post(login, {**credentials, "password": "wrong"},
                               secure=True, HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 401)
        response = client.post(login, credentials, secure=True, HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 200)
        csrf = response.data["csrfToken"]
        self.assertNotIn("access", response.data)
        for name in ("access_token", "refresh_token"):
            cookie = response.cookies[name]
            self.assertTrue(cookie["httponly"])
            self.assertTrue(cookie["secure"])
            self.assertEqual(cookie["samesite"], "Lax")

        tasks = reverse("api:task-list")
        self.assertEqual(client.get(tasks, secure=True).status_code, 200)
        self.assertEqual(client.post(tasks, {}, secure=True).status_code, 403)
        old_refresh = client.cookies["refresh_token"].value
        response = client.post(reverse("api:auth-refresh"), secure=True, HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 200)
        refresh = client.cookies["refresh_token"].value
        access = client.cookies["access_token"].value
        self.assertNotEqual(refresh, old_refresh)
        self.assertEqual(self.client.post(reverse("api:token-refresh"), {"refresh": old_refresh}).status_code, 401)

        logout = reverse("api:auth-logout")
        self.assertEqual(client.post(logout, secure=True).status_code, 403)
        response = client.post(logout, secure=True, HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 204)
        for name, path in (("access_token", "/api/"), ("refresh_token", "/api/auth/")):
            self.assertEqual(response.cookies[name]["max-age"], 0)
            self.assertEqual(response.cookies[name]["path"], path)
        self.assertEqual(self.client.get(tasks, HTTP_AUTHORIZATION=f"Bearer {access}").status_code, 401)
        self.assertEqual(self.client.post(reverse("api:token-refresh"), {"refresh": refresh}).status_code, 401)
