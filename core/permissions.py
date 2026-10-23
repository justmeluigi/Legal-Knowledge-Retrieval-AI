from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel


class ClearanceLevel(str, Enum):
    PUBLIC = "PUBLIC"                    # Available to everyone, guests, external auditors
    INTERNAL = "INTERNAL"                # Standard employee policies, general agreements
    LEGAL_COUNSEL = "LEGAL_COUNSEL"      # Sensitive commercial contracts, indemnities, settlement provisions
    EXECUTIVE_BOARD = "EXECUTIVE_BOARD"  # Strictly confidential M&A, executive compensation, strategic secrets


class UserRole(str, Enum):
    GUEST = "GUEST"
    EMPLOYEE = "EMPLOYEE"
    LEGAL_COUNSEL = "LEGAL_COUNSEL"
    EXECUTIVE_BOARD = "EXECUTIVE_BOARD"


# Clearance mapping: which clearance levels are accessible by each role
ROLE_PERMISSIONS: Dict[UserRole, List[ClearanceLevel]] = {
    UserRole.GUEST: [
        ClearanceLevel.PUBLIC
    ],
    UserRole.EMPLOYEE: [
        ClearanceLevel.PUBLIC,
        ClearanceLevel.INTERNAL
    ],
    UserRole.LEGAL_COUNSEL: [
        ClearanceLevel.PUBLIC,
        ClearanceLevel.INTERNAL,
        ClearanceLevel.LEGAL_COUNSEL
    ],
    UserRole.EXECUTIVE_BOARD: [
        ClearanceLevel.PUBLIC,
        ClearanceLevel.INTERNAL,
        ClearanceLevel.LEGAL_COUNSEL,
        ClearanceLevel.EXECUTIVE_BOARD
    ]
}


class RBACUserProfile(BaseModel):
    user_id: str
    name: str
    role: UserRole
    title: str
    description: str


# Pre-configured demo users representing different security personas
DEMO_USERS: Dict[str, RBACUserProfile] = {
    "alice_guest": RBACUserProfile(
        user_id="alice_guest",
        name="Alice Vance (Guest Auditor)",
        role=UserRole.GUEST,
        title="External Consultant",
        description="Public clearance only. Can only read Public Code of Conduct and external policies."
    ),
    "bob_employee": RBACUserProfile(
        user_id="bob_employee",
        name="Bob Martinez (Engineering Lead)",
        role=UserRole.EMPLOYEE,
        title="Staff Engineer",
        description="Internal clearance. Can read internal employee IP guidelines and standard operational agreements."
    ),
    "clara_legal": RBACUserProfile(
        user_id="clara_legal",
        name="Clara Sterling (Senior Counsel)",
        role=UserRole.LEGAL_COUNSEL,
        title="Senior Corporate Legal Counsel",
        description="Legal clearance. Access to commercial MSA contracts, uncapped indemnity clauses, and Data Protection Addenda."
    ),
    "david_executive": RBACUserProfile(
        user_id="david_executive",
        name="David Sterling (Board Director)",
        role=UserRole.EXECUTIVE_BOARD,
        title="Managing Partner & Board Member",
        description="Top Secret clearance. Full access to highly confidential M&A diligence, valuation, and executive equity agreements."
    )
}


def get_accessible_clearances(role: UserRole) -> List[str]:
    """Returns list of string clearance tags permitted for the given role."""
    return [level.value for level in ROLE_PERMISSIONS.get(role, [ClearanceLevel.PUBLIC])]
