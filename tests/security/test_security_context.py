from framework.security.security_context import SecurityContext


def test_security_context_stores_user_identity():

    context = SecurityContext(
        user_id="RECEPTION01",
        facility_ncid="1048021",
        role="Reception",
        permissions=["CHECK_IN", "VIEW_APPOINTMENT", "CREATE_ENCOUNTER"],
        session_id="SESSION001",
    )

    assert context.user_id == "RECEPTION01"
    assert context.facility_ncid == "1048021"
    assert context.role == "Reception"
    assert context.session_id == "SESSION001"


def test_security_context_allows_known_permission():

    context = SecurityContext(
        user_id="RECEPTION01",
        facility_ncid="1048021",
        role="Reception",
        permissions=["CHECK_IN", "VIEW_APPOINTMENT", "CREATE_ENCOUNTER"],
        session_id="SESSION001",
    )

    assert context.has_permission("CHECK_IN") is True


def test_security_context_rejects_unknown_permission():

    context = SecurityContext(
        user_id="RECEPTION01",
        facility_ncid="1048021",
        role="Reception",
        permissions=["CHECK_IN", "VIEW_APPOINTMENT", "CREATE_ENCOUNTER"],
        session_id="SESSION001",
    )

    assert context.has_permission("SIGN_PRESCRIPTION") is False


def test_security_context_can_be_converted_to_dictionary():

    context = SecurityContext(
        user_id="RECEPTION01",
        facility_ncid="1048021",
        role="Reception",
        permissions=["CHECK_IN", "VIEW_APPOINTMENT", "CREATE_ENCOUNTER"],
        session_id="SESSION001",
    )

    result = context.to_dict()

    assert result["userId"] == "RECEPTION01"
    assert result["facilityNcid"] == "1048021"
    assert result["role"] == "Reception"
    assert result["sessionId"] == "SESSION001"
    assert "CHECK_IN" in result["permissions"]