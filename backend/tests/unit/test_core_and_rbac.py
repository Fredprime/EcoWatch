"""Unit tests for core helpers, spatial validation, upload scanner, and RBAC matrix."""

import uuid
from datetime import UTC, datetime

import pytest

from ecowatch.core.config import Settings
from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.pagination import decode_cursor, encode_cursor
from ecowatch.core.security import (
    LocalTokenAuthProvider,
    generate_tracking_code,
    hash_password,
    hash_tracking_code,
    verify_password,
)
from ecowatch.core.spatial import (
    coarsen_point_wkt,
    format_point_wkt,
    parse_point_wkt,
    validate_wkt_geometry,
)
from ecowatch.core.storage import LocalFilesystemStorage
from ecowatch.modules.evidence.models import MetadataExtractionStatus, ScanStatus
from ecowatch.modules.evidence.scanner import (
    create_exif_stripped_preview,
    detect_mime_from_bytes,
    extract_image_metadata,
    is_mime_compatible,
    sanitize_filename,
    scan_evidence_bytes,
)
from ecowatch.modules.identity.permissions import (
    Permission,
    Principal,
    Role,
    SystemRole,
    ensure_not_self_submitted,
)


def test_production_secret_requires_override() -> None:
    with pytest.raises(ValueError, match="ECOWATCH_AUTH_SECRET"):
        Settings(environment="production")


def test_password_hash_and_verify() -> None:
    pwHash = hash_password("Secret#123", iterations=10_000)
    assert verify_password("Secret#123", pwHash) is True
    assert verify_password("wrong", pwHash) is False
    assert verify_password("Secret#123", "corrupt") is False


def test_token_issue_verify_and_tracking_hash() -> None:
    provider = LocalTokenAuthProvider("test-secret", ttlSeconds=60)
    userId = uuid.uuid4()
    token = provider.issue_token(userId)
    claims = provider.verify_token(token)
    assert claims is not None
    assert claims.userId == userId
    assert provider.verify_token(token + "tamper") is None

    code = generate_tracking_code()
    assert len(code) >= 22
    assert hash_tracking_code(code, "s1") == hash_tracking_code(code, "s1")
    assert hash_tracking_code(code, "s1") != hash_tracking_code(code, "s2")


def test_storage_prevents_path_traversal(tmp_path) -> None:
    storage = LocalFilesystemStorage(tmp_path / "storage")
    storage.put_bytes("originals/2026/11/abc.bin", b"hello")
    assert storage.get_bytes("originals/2026/11/abc.bin") == b"hello"
    for badKey in ["../escape.txt", "/abs/path.txt", "a/../../b.txt", ""]:
        with pytest.raises(DomainError) as excInfo:
            storage.put_bytes(badKey, b"bad")
        assert excInfo.value.code == ErrorCode.VALIDATION_ERROR


def test_spatial_and_cursor_helpers() -> None:
    wkt = validate_wkt_geometry("POLYGON((-1.6 6.6, -1.5 6.6, -1.5 6.7, -1.6 6.7, -1.6 6.6))")
    assert wkt.startswith("POLYGON")
    with pytest.raises(ValueError, match="bounds"):
        validate_wkt_geometry("POINT(200.0 10.0)")
    with pytest.raises(ValueError, match="Invalid WKT"):
        validate_wkt_geometry("NOT_WKT(1 2)")

    pt = format_point_wkt(-1.6244, 6.6885)
    assert parse_point_wkt(pt) == (-1.6244, 6.6885)
    assert coarsen_point_wkt(-1.6244, 6.6885) == "POINT(-1.62 6.69)"

    now = datetime(2026, 11, 18, 10, 0, tzinfo=UTC)
    uid = uuid.uuid4()
    cursor = encode_cursor(now, uid)
    assert decode_cursor(cursor) == (now, uid)
    with pytest.raises(DomainError) as excInfo:
        decode_cursor("bad-cursor")
    assert excInfo.value.code == ErrorCode.VALIDATION_ERROR


def test_rbac_deny_by_default_and_separation_of_duties() -> None:
    anon = Principal()
    assert anon.has_permission(Permission.OBS_CREATE) is True
    assert anon.has_permission(Permission.OBS_READ_REDACTED) is False
    assert anon.has_permission(Permission.CASE_CREATE) is False

    orgA = uuid.uuid4()
    orgB = uuid.uuid4()
    reviewerId = uuid.uuid4()
    reviewer = Principal(
        userId=reviewerId,
        memberships=((orgA, Role.REVIEWER),),
        isAuthenticated=True,
    )
    assert reviewer.has_permission(Permission.CASE_CREATE, orgA) is True
    assert reviewer.has_permission(Permission.CASE_CREATE, orgB) is False
    assert reviewer.has_permission(Permission.SOURCE_READ, orgA) is False

    sysAdmin = Principal(
        userId=uuid.uuid4(),
        systemRole=SystemRole.SYSTEM_ADMIN,
        isAuthenticated=True,
    )
    assert sysAdmin.has_permission(Permission.AUDIT_READ) is True
    assert sysAdmin.has_permission(Permission.CASE_TRANSITION_FIELD_VERIFIED) is False

    with pytest.raises(DomainError) as excInfo:
        ensure_not_self_submitted(reviewer, reviewerId)
    assert excInfo.value.code == ErrorCode.SELF_REVIEW_FORBIDDEN


def test_correlation_review_implies_correlation_read() -> None:
    """A role that may decide a suggestion must be able to list it.

    Otherwise the reviewer who is supposed to act on suggestions gets a 403 on
    the only endpoint that shows them, and the query silently returns nothing.
    """
    from ecowatch.modules.identity.permissions import ROLE_PERMISSIONS

    for role, granted in ROLE_PERMISSIONS.items():
        if Permission.CORRELATION_REVIEW in granted:
            assert Permission.CORRELATION_READ in granted, role
    # And the read-only end stays closed to contributors, who never review.
    assert Permission.CORRELATION_READ not in ROLE_PERMISSIONS[Role.REGISTERED_CONTRIBUTOR]


def test_scanner_magic_bytes_and_exif_stripping() -> None:
    from tests.conftest import make_jpeg_with_exif_bytes

    elfBytes = b"\x7fELF" + b"\x00" * 32
    detectedElf = detect_mime_from_bytes(elfBytes, "photo.jpg")
    assert detectedElf is None
    assert is_mime_compatible(detectedElf, "image/jpeg") is False

    assert sanitize_filename("../../evil/photo.jpg") == "photo.jpg"

    jpegBytes = make_jpeg_with_exif_bytes()
    assert detect_mime_from_bytes(jpegBytes, "field.jpg") == "image/jpeg"
    scanStatus, scanReason = scan_evidence_bytes(jpegBytes, "image/jpeg")
    assert scanStatus == ScanStatus.CLEAN
    assert scanReason is None
    metadataStatus, extractedMetadata = extract_image_metadata(jpegBytes)
    assert metadataStatus == MetadataExtractionStatus.EXTRACTED
    assert extractedMetadata is not None
    previewBytes, previewMime = create_exif_stripped_preview(jpegBytes, "image/jpeg")
    assert previewMime == "image/jpeg"
    assert previewBytes != jpegBytes
    assert b"EcoCamera" in jpegBytes
    assert b"EcoCamera" not in previewBytes
