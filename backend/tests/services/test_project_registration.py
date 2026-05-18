from app.services.project_registration import ProjectEnvironment, register_dependency_snapshot


class DummySession:
    def scalar(self, *_args, **_kwargs):
        return None

    def add(self, *_args, **_kwargs):
        raise AssertionError("register_dependency_snapshot should not add a project when it is missing")

    def flush(self, *_args, **_kwargs):
        raise AssertionError("register_dependency_snapshot should not flush when the project is missing")


def test_register_dependency_snapshot_requires_existing_project() -> None:
    session = DummySession()

    try:
        register_dependency_snapshot(
            db=session,
            project_name="missing-project",
            environment=ProjectEnvironment.DEV,
            api_key="some-api-key",
            dependencies=[],
        )
    except LookupError as exc:
        assert str(exc) == "project not found"
    else:
        raise AssertionError("Expected LookupError for missing project")