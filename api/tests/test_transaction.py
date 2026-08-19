import unittest
from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.usecase._transaction import transactional


class _SuccessfulUsecase:
    def __init__(self, db: Session):
        self.db = db

    @transactional
    def execute(self) -> str:
        return "result"


class _FailingUsecase:
    def __init__(self, db: Session):
        self.db = db

    @transactional
    def execute(self) -> None:
        raise ValueError("business flow failed")


class TransactionBoundaryTest(unittest.TestCase):
    def test_session_keeps_returned_entities_loaded_after_commit(self):
        self.assertFalse(SessionLocal.kw["expire_on_commit"])

    def test_transactional_commits_successful_primary_flow(self):
        db = Mock(spec=Session)

        result = _SuccessfulUsecase(db).execute()

        self.assertEqual(result, "result")
        db.commit.assert_called_once_with()
        db.rollback.assert_not_called()

    def test_transactional_rolls_back_failed_primary_flow(self):
        db = Mock(spec=Session)

        with self.assertRaisesRegex(ValueError, "business flow failed"):
            _FailingUsecase(db).execute()

        db.commit.assert_not_called()
        db.rollback.assert_called_once_with()

    def test_transactional_rolls_back_failed_commit(self):
        db = Mock(spec=Session)
        db.commit.side_effect = RuntimeError("commit failed")

        with self.assertRaisesRegex(RuntimeError, "commit failed"):
            _SuccessfulUsecase(db).execute()

        db.rollback.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
