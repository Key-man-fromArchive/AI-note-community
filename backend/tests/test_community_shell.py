from __future__ import annotations

import base64
from typing import Any

import pytest
from fastapi import HTTPException


def _owner_user(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": session["user_id"],
        "email": session["email"],
        "name": session["name"],
        "org_id": session["org_id"],
        "org_slug": session["org_slug"],
        "role": session["role"],
    }


@pytest.mark.asyncio
async def test_signup_initializes_workspace_and_default_notebook(app_modules: tuple[Any, Any]) -> None:
    main_module, store_module = app_modules

    session = await main_module.member_signup(
        main_module.SignupRequest(
            email="owner@example.com",
            password="strongpass1",
            name="Owner",
            org_name="Test Org",
            org_slug="test-org",
        )
    )

    state = store_module.store.load()

    assert session["role"] == "owner"
    assert state["setup"]["initialized"] is True
    assert state["organization"]["slug"] == "test-org"
    assert state["notebooks"] == [
        {
            "id": 1,
            "name": "General",
            "description": "Default notebook",
            "category": None,
            "note_count": 0,
        }
    ]


@pytest.mark.asyncio
async def test_invited_member_can_activate_account_via_signup(app_modules: tuple[Any, Any]) -> None:
    main_module, store_module = app_modules

    owner_session = await main_module.member_signup(
        main_module.SignupRequest(
            email="owner@example.com",
            password="strongpass1",
            name="Owner",
            org_name="Test Org",
            org_slug="test-org",
        )
    )
    owner_user = _owner_user(owner_session)

    invite = await main_module.invite_member(
        main_module.InviteRequest(email="member@example.com", role="member"),
        current_user=owner_user,
    )
    member_session = await main_module.member_signup(
        main_module.SignupRequest(
            email="member@example.com",
            password="memberpass1",
            name="Member",
        )
    )

    state = store_module.store.load()
    invited_user = next(user for user in state["users"] if user["email"] == "member@example.com")

    assert invite["email"] == "member@example.com"
    assert member_session["role"] == "member"
    assert invited_user["is_pending"] is False
    assert invited_user["accepted_at"] is not None


@pytest.mark.asyncio
async def test_uninvited_member_cannot_join_initialized_workspace(app_modules: tuple[Any, Any]) -> None:
    main_module, _ = app_modules

    await main_module.member_signup(
        main_module.SignupRequest(
            email="owner@example.com",
            password="strongpass1",
            name="Owner",
            org_name="Test Org",
            org_slug="test-org",
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        await main_module.member_signup(
            main_module.SignupRequest(
                email="outsider@example.com",
                password="memberpass1",
                name="Outsider",
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "invite_required"


@pytest.mark.asyncio
async def test_search_and_graph_support_unicode_note_content(app_modules: tuple[Any, Any]) -> None:
    main_module, _ = app_modules

    owner_session = await main_module.member_signup(
        main_module.SignupRequest(
            email="owner@example.com",
            password="strongpass1",
            name="Owner",
            org_name="Test Org",
            org_slug="test-org",
        )
    )
    owner_user = _owner_user(owner_session)

    await main_module.create_note(
        main_module.NoteCreateRequest(
            title="한글 실험 노트",
            content="세포 배양 결과와 control comparison",
            notebook="General",
        ),
        current_user=owner_user,
    )
    await main_module.create_note(
        main_module.NoteCreateRequest(
            title="Follow-up",
            content="세포 배양 repeat run with control adjustments",
            notebook="General",
        ),
        current_user=owner_user,
    )

    search = await main_module.search_notes(
        q="세포 배양",
        type="search",
        limit=20,
        offset=0,
        current_user=owner_user,
    )
    graph = await main_module.graph_data(limit=20, current_user=owner_user)

    assert search["total"] == 2
    assert len(search["results"]) == 2
    assert len(graph["nodes"]) == 2
    assert len(graph["links"]) == 1


@pytest.mark.asyncio
async def test_snapshot_restore_recovers_previous_note_state(app_modules: tuple[Any, Any]) -> None:
    main_module, store_module = app_modules

    owner_session = await main_module.member_signup(
        main_module.SignupRequest(
            email="owner@example.com",
            password="strongpass1",
            name="Owner",
            org_name="Test Org",
            org_slug="test-org",
        )
    )
    owner_user = _owner_user(owner_session)

    await main_module.create_note(
        main_module.NoteCreateRequest(
            title="Baseline",
            content="initial result",
            notebook="General",
        ),
        current_user=owner_user,
    )
    snapshot = await main_module.snapshot_full(current_user=owner_user)
    await main_module.create_note(
        main_module.NoteCreateRequest(
            title="Temporary",
            content="to be removed by restore",
            notebook="General",
        ),
        current_user=owner_user,
    )

    restored = await main_module.snapshot_restore(snapshot["snapshot_id"], current_user=owner_user)
    state = store_module.store.load()

    assert restored["snapshot_id"] == snapshot["snapshot_id"]
    assert [note["title"] for note in state["notes"]] == ["Baseline"]
    assert state["snapshots"][0]["snapshot_id"] == snapshot["snapshot_id"]


@pytest.mark.asyncio
async def test_invalid_refresh_token_returns_http_401(app_modules: tuple[Any, Any]) -> None:
    main_module, _ = app_modules

    with pytest.raises(HTTPException) as exc_info:
        await main_module.auth_refresh(main_module.RefreshRequest(refresh_token="invalid-token"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "invalid_refresh_token"


def test_invalid_access_token_returns_http_401(app_modules: tuple[Any, Any]) -> None:
    main_module, _ = app_modules

    with pytest.raises(HTTPException) as exc_info:
        main_module.get_current_user("Bearer invalid-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "invalid_token"


@pytest.mark.asyncio
async def test_feedback_submission_is_saved_without_github(app_modules: tuple[Any, Any]) -> None:
    main_module, store_module = app_modules

    owner_session = await main_module.member_signup(
        main_module.SignupRequest(
            email="owner@example.com",
            password="strongpass1",
            name="Owner",
            org_name="Test Org",
            org_slug="test-org",
        )
    )
    owner_user = _owner_user(owner_session)

    feedback = await main_module.create_feedback(
        main_module.FeedbackCreateRequest(
            title="검색 결과 설명이 더 필요합니다",
            category="ux",
            priority="high",
            page="/search",
            message="결과가 왜 나왔는지 설명과 다음 액션이 보이면 좋겠습니다.",
            create_github_issue=False,
        ),
        current_user=owner_user,
    )
    listing = await main_module.list_feedback(current_user=owner_user)
    state = store_module.store.load()

    assert feedback["github_sync_status"] == "not_requested"
    assert listing["total"] == 1
    assert listing["items"][0]["feedback_id"] == feedback["feedback_id"]
    assert state["feedback"][0]["title"] == "검색 결과 설명이 더 필요합니다"


@pytest.mark.asyncio
async def test_feedback_submission_can_sync_to_github_issue(
    app_modules: tuple[Any, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    main_module, _ = app_modules

    owner_session = await main_module.member_signup(
        main_module.SignupRequest(
            email="owner@example.com",
            password="strongpass1",
            name="Owner",
            org_name="Test Org",
            org_slug="test-org",
        )
    )
    owner_user = _owner_user(owner_session)

    monkeypatch.setenv("GITHUB_FEEDBACK_REPO", "example/ainote-community")
    monkeypatch.setenv("GITHUB_FEEDBACK_TOKEN", "token")
    main_module.get_settings.cache_clear()

    async def fake_create_issue(*, title: str, body: str, labels: list[str]) -> dict[str, Any]:
        assert "검색" in title
        assert "Feedback ID" in body
        assert "category:search" in labels
        return {
            "status": "created",
            "issue_number": 42,
            "issue_url": "https://github.com/example/ainote-community/issues/42",
            "error": None,
        }

    monkeypatch.setattr(main_module, "create_github_issue", fake_create_issue)

    feedback = await main_module.create_feedback(
        main_module.FeedbackCreateRequest(
            title="검색 필터가 필요합니다",
            category="search",
            priority="medium",
            page="/search",
            message="태그와 노트북 기준으로 바로 필터링할 수 있으면 더 좋겠습니다.",
            create_github_issue=True,
        ),
        current_user=owner_user,
    )
    config = await main_module.feedback_config(current_user=owner_user)

    assert config["github_enabled"] is True
    assert config["github_repo"] == "example/ainote-community"
    assert feedback["github_sync_status"] == "created"
    assert feedback["github_issue_number"] == 42


@pytest.mark.asyncio
async def test_feedback_screenshot_is_saved_and_addressable(app_modules: tuple[Any, Any]) -> None:
    main_module, store_module = app_modules

    owner_session = await main_module.member_signup(
        main_module.SignupRequest(
            email="owner@example.com",
            password="strongpass1",
            name="Owner",
            org_name="Test Org",
            org_slug="test-org",
        )
    )
    owner_user = _owner_user(owner_session)
    pixel = base64.b64encode(
        bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
            "0000000D49444154789C6360606060000000050001A5F645400000000049454E44AE426082"
        )
    ).decode()

    feedback = await main_module.create_feedback(
        main_module.FeedbackCreateRequest(
            title="스크린샷 첨부 테스트",
            category="ux",
            priority="medium",
            page="/feedback",
            message="이미지 첨부가 로컬에 저장되고 다시 읽혀야 합니다.",
            create_github_issue=False,
            screenshot_names=["capture.png", "capture-2.png"],
            screenshot_data_urls=[
                f"data:image/png;base64,{pixel}",
                f"data:image/png;base64,{pixel}",
            ],
        ),
        current_user=owner_user,
    )
    state = store_module.store.load()
    first_asset = feedback["screenshots"][0]
    second_asset = feedback["screenshots"][1]
    first_path = store_module.store.settings.feedback_assets_dir / first_asset["asset_name"]
    second_path = store_module.store.settings.feedback_assets_dir / second_asset["asset_name"]

    assert len(feedback["screenshots"]) == 2
    assert first_asset["asset_name"] == "feedback-00001-1.png"
    assert first_asset["asset_url"] == "/api/feedback/assets/feedback-00001-1.png"
    assert second_asset["asset_name"] == "feedback-00001-2.png"
    assert state["feedback"][0]["screenshots"][0]["original_name"] == "capture.png"
    assert first_path.exists() is True
    assert second_path.exists() is True


@pytest.mark.asyncio
async def test_feedback_rejects_more_than_three_screenshots(app_modules: tuple[Any, Any]) -> None:
    main_module, _ = app_modules

    owner_session = await main_module.member_signup(
        main_module.SignupRequest(
            email="owner@example.com",
            password="strongpass1",
            name="Owner",
            org_name="Test Org",
            org_slug="test-org",
        )
    )
    owner_user = _owner_user(owner_session)
    pixel = base64.b64encode(
        bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
            "0000000D49444154789C6360606060000000050001A5F645400000000049454E44AE426082"
        )
    ).decode()

    with pytest.raises(HTTPException) as exc_info:
        await main_module.create_feedback(
            main_module.FeedbackCreateRequest(
                title="이미지 제한 테스트",
                category="ux",
                priority="medium",
                page="/feedback",
                message="스크린샷이 3장을 넘으면 서버가 거절해야 합니다.",
                create_github_issue=False,
                screenshot_names=["1.png", "2.png", "3.png", "4.png"],
                screenshot_data_urls=[
                    f"data:image/png;base64,{pixel}",
                    f"data:image/png;base64,{pixel}",
                    f"data:image/png;base64,{pixel}",
                    f"data:image/png;base64,{pixel}",
                ],
            ),
            current_user=owner_user,
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "too_many_screenshots"
