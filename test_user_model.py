"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("test1", "email1@email.com", "password", None)
        uid1 = 1111
        u1.id = uid1

        u2 = User.signup("test2", "email2@email.com", "password", None)
        uid2 = 2222
        u2.id = uid2

        db.session.commit()

        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)

        self.u1 = u1
        self.uid1 = uid1

        self.u2 = u2
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(email="test@test.com", username="testuser", password="HASHED_PASSWORD")

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        self.assertEqual(
            User.__repr__(self.u2), "<User #2222: test2, email2@email.com>"
        )

    def test_is_following(self):
        # u2 append u1.following
        self.u2.following.append(self.u1)
        db.session.commit()

        self.assertTrue(User.is_following(self.u2, self.u1))

    def test_is_followed_by(self):
        self.u2.following.append(self.u1)
        db.session.commit()

        self.assertTrue(User.is_followed_by(self.u1, self.u2))

    def test_not_is_followed_by(self):
        self.u2.following.append(self.u1)
        db.session.commit()

        self.assertFalse(User.is_followed_by(self.u2, self.u1))

    # Does User.create successfully create a new user given valid credentials?
    def test_signup(self):
        u3 = User.signup(
            "test",
            "test@test.test",
            "testingpass",
            "none",
        )
        u3id = 123456
        u3.id = u3id

        db.session.commit()

        u3_test = User.query.get(u3id)
        self.assertIsNotNone(u3_test)
        self.assertEqual(u3.username, "test")
        self.assertEqual(u3.email, "test@test.test")
        self.assertNotEqual(u3.password, "testingpass")
        self.assertTrue(u3.password.startswith("$2b$"))

    # Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?
    def test_signup_failed(self):
        invalid = User.signup(
            None,
            "test@test.com",
            "testingpass",
            None,
        )

        uid = 1234565
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    # Does User.authenticate successfully return a user when given a valid username and password?
    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)

    # Does User.authenticate fail to return a user when the username is invalid?
    def test_invalid_user(self):
        self.assertFalse(User.authenticate("badusername", "password"))

    # Does User.authenticate fail to return a user when the password is invalid?
    def test_invalid_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "badpassword"))
