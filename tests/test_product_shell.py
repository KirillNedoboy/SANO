from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_workspace_uses_localized_shared_shell_in_english_and_russian(
    product_core_client: TestClient,
) -> None:
    english = product_core_client.get("/workspace")
    assert english.status_code == 200
    assert '<html lang="en">' in english.text
    assert 'class="product-shell__sidebar"' in english.text
    assert 'aria-current="page"' in english.text
    assert "Overview" in english.text
    assert 'id="product-shell-locale"' in english.text
    assert 'value="ru"' in english.text

    product_core_client.cookies.set("opencare_locale", "ru", path="/")
    russian = product_core_client.get("/workspace")
    assert russian.status_code == 200
    assert '<html lang="ru">' in russian.text
    assert "Обзор" in russian.text
    assert "Язык" in russian.text
    assert "Пользователь не выбран" in russian.text
    assert 'id="product-shell-person"' in russian.text


def test_genetics_uses_application_shell_and_preserves_local_navigation(
    product_core_client: TestClient,
) -> None:
    response = product_core_client.get("/genetics")
    assert response.status_code == 200
    assert 'href="/genetics" aria-current="page"' in response.text
    assert 'class="workspace-tabs"' in response.text
    assert 'id="tab-overview"' in response.text
    assert 'id="panel-research"' in response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_shared_shell_person_slot_truthfully_represents_empty_and_selected_state(
    product_core_client: TestClient,
) -> None:
    empty = product_core_client.get("/workspace")
    assert empty.status_code == 200
    assert "No person selected" in empty.text
    assert 'data-active-person-id=""' in empty.text

    csrf = product_core_client.cookies.get("opencare_csrf")
    assert csrf is not None
    selected = product_core_client.put(
        "/api/family-access/v1/active-person",
        json={"person_id": "person-1"},
        headers={"origin": "http://testserver", "x-opencare-csrf": csrf},
    )
    assert selected.status_code == 204
    rendered = product_core_client.get("/workspace")
    assert rendered.status_code == 200
    assert "Selected person" in rendered.text
    assert 'data-active-person-id="person-1"' in rendered.text


def test_invalid_locale_cannot_change_auth_or_inject_markup(
    product_core_client: TestClient,
) -> None:
    product_core_client.cookies.set("opencare_locale", 'ru"><script>alert(1)</script>', path="/")
    rendered = product_core_client.get("/workspace")
    assert rendered.status_code == 200
    assert '<html lang="en">' in rendered.text
    assert "<script>alert(1)</script>" not in rendered.text

    product_core_client.cookies.clear()
    protected = product_core_client.get("/workspace", follow_redirects=False)
    assert protected.status_code == 307
    assert protected.headers["location"] == "/login?next=%2Fworkspace"


def test_shared_shell_does_not_create_new_backend_routes(
    product_core_client: TestClient,
) -> None:
    response = product_core_client.get("/settings", follow_redirects=False)
    assert response.status_code == 404
    assert product_core_client.get("/family-access#account-settings").status_code == 200


def test_authenticated_chat_renders_shared_shell_and_localized_content(
    product_core_client: TestClient,
) -> None:
    selected = product_core_client.put(
        "/api/family-access/v1/active-person", json={"person_id": "person-1"}
    )
    assert selected.status_code == 204
    english = product_core_client.get("/chat")
    assert english.status_code == 200
    assert '<html lang="en">' in english.text
    assert 'class="product-shell__sidebar"' in english.text
    assert 'href="/chat" aria-current="page"' in english.text
    assert 'class="chat-content"' in english.text
    assert 'class="chat-sidebar"' not in english.text
    assert "Ask about your recorded vault" in english.text

    product_core_client.cookies.set("opencare_locale", "ru", path="/")
    russian = product_core_client.get("/chat")
    assert russian.status_code == 200
    assert '<html lang="ru">' in russian.text
    assert "Спросите о записанных данных" in russian.text
    assert "Отправить" in russian.text


def test_demo_chat_keeps_demo_endpoint_without_authenticated_shell(
    product_core_client: TestClient,
) -> None:
    demo = product_core_client.get("/demo/chat")
    assert demo.status_code == 200
    assert 'data-chat-endpoint="/api/demo/chat"' in demo.text
    assert 'class="product-shell__sidebar"' not in demo.text


def test_public_auth_uses_canonical_ui_tokens_without_legacy_aliases() -> None:
    public_auth = (Path("app") / "static" / "public_auth.css").read_text(encoding="utf-8")
    shell = (Path("app") / "static" / "product_shell.css").read_text(encoding="utf-8")

    assert "--shell-" not in public_auth
    assert "var(--focus-state)" not in public_auth
    assert "var(--success)" not in public_auth
    assert "var(--danger)" not in public_auth
    assert "--shell-" not in shell
    assert "--focus-state" not in shell
    assert "  --success:" not in shell
    assert "  --danger:" not in shell


def test_primary_navigation_exposes_stable_keys_and_existing_destinations() -> None:
    shell = (Path("app") / "templates" / "product_shell.html").read_text(encoding="utf-8")
    expected = {
        "documents": "/documents",
        "assistant": "/chat",
        "health": "/workspace#records",
        "genetics": "/genetics",
        "family": "/family-access",
        "settings": "/family-access#account-settings",
    }
    for key, href in expected.items():
        assert f'data-nav-key="{key}"' in shell
        assert f'href="{href}"' in shell


def test_primary_navigation_keeps_optional_sections_after_health() -> None:
    shell = (Path("app") / "templates" / "product_shell.html").read_text(encoding="utf-8")
    import re

    assert re.findall(r'data-nav-key="([^"]+)"', shell) == [
        "documents",
        "assistant",
        "health",
        "genetics",
        "family",
        "settings",
    ]
    assert shell.index('data-nav-key="health"') < shell.index('role="separator"')
    assert shell.index('role="separator"') < shell.index('data-nav-key="genetics"')


def test_sano_brand_and_common_palette_cover_public_and_product_surfaces(
    product_core_client: TestClient,
) -> None:
    from pathlib import Path

    selected = product_core_client.put(
        "/api/family-access/v1/active-person", json={"person_id": "person-1"}
    )
    assert selected.status_code == 204
    for path in (
        "/",
        "/login",
        "/register",
        "/invite",
        "/documents",
        "/chat",
        "/workspace",
        "/genetics",
        "/family-access",
    ):
        response = product_core_client.get(path)
        assert response.status_code == 200, path
        assert "OpenCare" not in response.text, path

    shell = (Path("app") / "templates" / "product_shell.html").read_text(encoding="utf-8")
    auth = (Path("app") / "templates" / "public_auth_shell.html").read_text(encoding="utf-8")
    tokens = (Path("app") / "static" / "brand.css").read_text(encoding="utf-8")
    assert "path='/brand.css'" in shell
    assert "path='/brand.css'" in auth
    for color in ("#EDF2ED", "#F8FAF7", "#15231E", "#176B59", "#C66B4F"):
        assert color.lower() in tokens.lower()


def test_public_landing_localizes_archive_first_message_and_generated_hero(
    product_core_client: TestClient,
) -> None:
    product_core_client.cookies.clear()
    english = product_core_client.get("/", follow_redirects=False)
    assert english.status_code == 200
    assert "Health documents you can find when you need them" in english.text
    assert "Start with the documents you already have" in english.text
    assert "PDF / TXT / JPG / PNG" in english.text
    assert "Genetics is an optional section" in english.text
    assert "Start with one document" in english.text
    assert "You can also run SANO on your own server." in english.text
    assert "No DNA test needed" not in english.text
    assert "Finally in one place" not in english.text
    assert "/brand/sano-hero-x1.webp" in english.text

    product_core_client.cookies.set("opencare_locale", "ru", path="/")
    russian = product_core_client.get("/", follow_redirects=False)
    assert "Медицинские документы, к которым легко вернуться" in russian.text
    assert "Начните с документов, которые у вас уже есть" in russian.text
    assert "Генетика — дополнительный раздел" in russian.text
    assert "Начните с одного документа" in russian.text
    assert "При желании SANO можно разместить на собственном сервере." in russian.text
    assert "Анализ ДНК не нужен" not in russian.text
    assert "Наконец в одном месте" not in russian.text


def test_product_shell_hash_navigation_is_exclusive_and_non_persistent() -> None:
    script = (Path("app") / "static" / "product_shell.js").read_text(encoding="utf-8")
    for fragment in (
        '"/workspace"',
        '"/documents"',
        '"/chat"',
        '"/genetics"',
        '"/family-access"',
        '"#account-settings"',
        '"hashchange"',
        '"aria-current"',
        '"is-active"',
    ):
        assert fragment in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script


def test_account_password_form_has_hidden_username_autocomplete_field() -> None:
    template = (Path("app") / "templates" / "family_access_workspace.html").read_text(
        encoding="utf-8"
    )
    styles = (Path("app") / "static" / "family_access_workspace.css").read_text(encoding="utf-8")
    form_start = template.index('<form id="change-password-form">')
    form_end = template.index("</form>", form_start)
    form = template[form_start:form_end]
    assert 'autocomplete="username"' in form
    assert 'type="text"' in form
    assert 'class="family-visually-hidden"' in form
    assert "width: 1px !important" in styles
    assert "height: 1px !important" in styles
