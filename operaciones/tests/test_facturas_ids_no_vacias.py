import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_no_permite_facturas_ids_vacias():
    api = APIClient()

    resp = api.post(
        "/api/operaciones/",
        {
            "cliente": 1,
            "facturas_ids": [],
        },
        format="json",
    )

    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "facturas_ids" in body["errors"]
