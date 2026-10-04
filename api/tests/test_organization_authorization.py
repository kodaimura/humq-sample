import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from app.core.error import AppError, ErrorCode
from app.usecase.organizations._authorization import RequireOrganizationRole


class OrganizationAuthorizationTest(unittest.TestCase):
    def setUp(self):
        self.db = Mock(spec=Session)
        organization_patch = patch(
            "app.usecase.organizations._authorization.OrganizationModule"
        )
        member_patch = patch(
            "app.usecase.organizations._authorization.OrganizationMemberModule"
        )
        self.organizations = organization_patch.start().return_value
        self.members = member_patch.start().return_value
        self.addCleanup(organization_patch.stop)
        self.addCleanup(member_patch.stop)
        self.authorization = RequireOrganizationRole(self.db)

    def require(self):
        self.authorization.run(
            organization_id=7, account_id=11, allowed_roles={"ADMIN"}
        )

    def test_missing_organization_is_rejected_before_member_lookup(self):
        self.organizations.get_by_id.return_value = None

        with self.assertRaises(AppError) as raised:
            self.require()

        self.assertEqual(raised.exception.code, ErrorCode.ORGANIZATION_NOT_FOUND.value)
        self.members.get.assert_not_called()

    def test_missing_or_unallowed_member_is_rejected(self):
        self.organizations.get_by_id.return_value = object()
        for member in (None, SimpleNamespace(role="SALES")):
            with self.subTest(member=member):
                self.members.get.return_value = member
                with self.assertRaises(AppError) as raised:
                    self.require()
                self.assertEqual(raised.exception.code, ErrorCode.ACCESS_DENIED.value)

    def test_allowed_member_passes_without_finalizing_transaction(self):
        self.organizations.get_by_id.return_value = object()
        self.members.get.return_value = SimpleNamespace(role="ADMIN")

        self.require()

        self.organizations.get_by_id.assert_called_once_with(7)
        self.members.get.assert_called_once_with(organization_id=7, account_id=11)
        self.db.commit.assert_not_called()
        self.db.rollback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
