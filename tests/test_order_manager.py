import pytest
from app import create_app, db
from app.models import User, Order, Trade
from app.orders.manager import place_order


@pytest.fixture(scope="module")
def test_client():
    flask_app = create_app("testing")

    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            db.create_all()
            yield testing_client
            db.drop_all()


@pytest.fixture(scope="function")
def new_user(test_client):
    with test_client.application.app_context():
        user = User(username="testuser", email="test@example.com")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        # Refresh the user object to ensure it's bound to the session
        user = db.session.merge(user)
        return user


def test_place_paper_order(test_client):
    """
    GIVEN a user and an order payload for a paper trade
    WHEN the place_order function is called
    THEN a new Order and Trade should be created in the database
    """
    with test_client.application.app_context():
        # Create user within the test context
        user = User(username="testuser", email="test@example.com")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

        order_payload = {
            "symbol": "TEST",
            "quantity": 10,
            "order_type": "market",
            "side": "buy",
            "is_paper": True,
        }

        order = place_order(user, order_payload)

        assert order.id is not None
        assert order.user_id == user.id
        assert order.is_paper is True
        assert order.status in ["filled", "partial"]

        trade = Trade.query.filter_by(order_id=order.id).first()
        assert trade is not None
        assert trade.quantity > 0
