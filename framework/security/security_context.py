class SecurityContext:
    def __init__(
        self,
        user_id: str,
        facility_ncid: str,
        role: str,
        permissions: list[str],
        session_id: str,
    ):
        self.user_id = user_id
        self.facility_ncid = facility_ncid
        self.role = role
        self.permissions = permissions
        self.session_id = session_id

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def to_dict(self) -> dict:
        return {
            "userId": self.user_id,
            "facilityNcid": self.facility_ncid,
            "role": self.role,
            "permissions": self.permissions,
            "sessionId": self.session_id,
        }