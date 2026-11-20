"""Integration tests for governed controlled-vocabulary configuration.

All records are temporary, created inside the isolated test database, and
removed by fixture teardown. No product seed data is used.
"""

import uuid

import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.identity.permissions import Role, SystemRole
from ecowatch.modules.vocabularies.models import VocabularyTerm
from tests.conftest import auth_headers, create_temp_org, create_temp_user

BASE = "/api/v1/vocabularies/terms"


def _admin(dbSession: Session, authProvider: LocalTokenAuthProvider) -> dict[str, str]:
    user = create_temp_user(dbSession, systemRole=SystemRole.SYSTEM_ADMIN)
    return auth_headers(authProvider, user)


def _term(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "vocabularyKey": "water_quality",
        "code": "TURBIDITY",
        "label": "Turbidity",
        "description": "Visibility of suspended particles.",
    }
    payload.update(overrides)
    return payload


def test_system_admin_can_create_list_update_and_deactivate_terms(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    headers = _admin(dbSession, authProvider)

    created = client.post(BASE, headers=headers, json=_term())
    assert created.status_code == 201, created.text
    term = created.json()
    assert term["vocabularyKey"] == "water_quality"
    assert term["code"] == "TURBIDITY"
    assert term["label"] == "Turbidity"
    assert term["isActive"] is True
    assert term["createdAt"] and term["updatedAt"]

    other = client.post(BASE, headers=headers, json=_term(code="PH"))
    assert other.status_code == 201, other.text

    listed = client.get(BASE, headers=headers, params={"vocabularyKey": "water_quality"})
    assert listed.status_code == 200, listed.text
    assert {item["code"] for item in listed.json()["items"]} == {"TURBIDITY", "PH"}
    assert client.get(
        BASE, headers=headers, params={"vocabularyKey": "air_quality"}
    ).json()["items"] == []

    updated = client.patch(
        f"{BASE}/{term['id']}",
        headers=headers,
        json={"label": "Turbidity (NTU)", "description": "Suspended particle load."},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["label"] == "Turbidity (NTU)"
    assert updated.json()["description"] == "Suspended particle load."

    deactivated = client.post(f"{BASE}/{term['id']}/deactivate", headers=headers)
    assert deactivated.status_code == 200, deactivated.text
    assert deactivated.json()["isActive"] is False

    reactivated = client.patch(
        f"{BASE}/{term['id']}", headers=headers, json={"isActive": True}
    )
    assert reactivated.status_code == 200, reactivated.text
    assert reactivated.json()["isActive"] is True

    events = dbSession.scalars(
        sa.select(AuditEvent)
        .where(AuditEvent.targetType == "vocabularyTerm")
        .order_by(AuditEvent.occurredAt)
    ).all()
    assert [event.action for event in events] == [
        "vocabulary.term.created",
        "vocabulary.term.created",
        "vocabulary.term.updated",
        "vocabulary.term.deactivated",
        "vocabulary.term.updated",
    ]
    assert all(event.actorRole == "system_admin" for event in events)
    assert all(event.details["vocabularyKey"] == "water_quality" for event in events)
    assert all(event.details["code"] in {"TURBIDITY", "PH"} for event in events)
    assert all(event.actorUserId is not None for event in events)


def test_vocabulary_endpoints_require_system_admin(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    orgId = create_temp_org(dbSession).id
    orgAdmin = create_temp_user(dbSession, memberships=[(orgId, Role.ORGANISATION_ADMIN)])
    reviewer = create_temp_user(dbSession, memberships=[(orgId, Role.REVIEWER)])
    termId = uuid.uuid4()

    calls = [
        ("post", BASE, _term()),
        ("get", BASE, None),
        ("patch", f"{BASE}/{termId}", {"label": "Changed"}),
        ("post", f"{BASE}/{termId}/deactivate", None),
    ]
    deniedHeaders = (
        {},
        auth_headers(authProvider, orgAdmin),
        auth_headers(authProvider, reviewer),
    )
    for method, path, body in calls:
        for headers in deniedHeaders:
            response = client.request(
                method, path, headers=headers, json=body if body is not None else None
            )
            expected = 401 if not headers else 403
            assert response.status_code == expected, (method, path, response.text)
            if expected == 403:
                assert response.json()["code"] == "FORBIDDEN"


def test_vocabulary_input_validation_and_conflicts(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    headers = _admin(dbSession, authProvider)

    assert client.post(BASE, headers=headers, json=_term(label="   ")).status_code == 422
    assert client.post(BASE, headers=headers, json=_term(code="bad code!")).status_code == 422
    assert client.patch(
        f"{BASE}/{uuid.uuid4()}", headers=headers, json={}
    ).status_code == 422

    assert client.post(BASE, headers=headers, json=_term()).status_code == 201
    duplicate = client.post(BASE, headers=headers, json=_term())
    assert duplicate.status_code == 409, duplicate.text
    assert duplicate.json()["field"] == "code"

    missingId = uuid.uuid4()
    assert client.patch(
        f"{BASE}/{missingId}", headers=headers, json={"isActive": False}
    ).status_code == 404
    assert client.post(f"{BASE}/{missingId}/deactivate", headers=headers).status_code == 404

    assert dbSession.scalars(sa.select(VocabularyTerm)).all() != []


def test_vocabulary_list_is_cursor_paginated(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    headers = _admin(dbSession, authProvider)
    for index in range(4):
        response = client.post(BASE, headers=headers, json=_term(code=f"CODE_{index}"))
        assert response.status_code == 201, response.text

    first = client.get(BASE, headers=headers, params={"limit": 2})
    assert first.status_code == 200, first.text
    assert len(first.json()["items"]) == 2
    assert first.json()["hasMore"] is True

    second = client.get(
        BASE, headers=headers, params={"limit": 2, "cursor": first.json()["nextCursor"]}
    )
    assert second.status_code == 200, second.text
    assert len(second.json()["items"]) == 2
    assert second.json()["hasMore"] is False
    assert not {item["code"] for item in first.json()["items"]} & {
        item["code"] for item in second.json()["items"]
    }
