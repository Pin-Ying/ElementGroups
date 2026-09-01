"""登入方式的設定邏輯。

GOOGLE_LOGIN_ENABLED 與 PASSWORD_LOGIN_ENABLED 的連動關係決定了「後台現在
有哪些路可以進來」，是這個專案最容易把自己鎖在門外的地方。這些組合在功能
開發時驗過一遍，收進來是因為那條規則只有一行，很容易在之後改動時被改壞，
而壞掉的後果是站長登不進後台。

特別要保住的是**逃生門**：把 PASSWORD_LOGIN_ENABLED 明確設成 true 時，
不論 Google 開著沒有，帳密登入都要能用。
"""

import os

import pytest

from conftest import FAKE_ENV, load_app_module


@pytest.fixture
def settings_factory(monkeypatch):
    """回傳一個工廠：給定兩個開關的值，產生對應的 Settings 實例。"""
    for key, value in FAKE_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("GOOGLE_LOGIN_ENABLED", raising=False)
    monkeypatch.delenv("PASSWORD_LOGIN_ENABLED", raising=False)

    config = load_app_module("config")

    def make(google=None, password=None):
        if google is None:
            monkeypatch.delenv("GOOGLE_LOGIN_ENABLED", raising=False)
        else:
            monkeypatch.setenv("GOOGLE_LOGIN_ENABLED", google)
        if password is None:
            monkeypatch.delenv("PASSWORD_LOGIN_ENABLED", raising=False)
        else:
            monkeypatch.setenv("PASSWORD_LOGIN_ENABLED", password)
        # _env_file=None：不要讀到開發機上真實的 backend/.env
        return config.Settings(_env_file=None)

    return make


class TestLoginMethodInterlock:
    """不設 PASSWORD_LOGIN_ENABLED 時，帳密登入與 Google 登入互斥。"""

    def test_default_is_password_only(self, settings_factory):
        """安裝預設：Google 沒開，走帳密登入。"""
        s = settings_factory()
        assert s.GOOGLE_LOGIN_ENABLED is False
        assert s.password_login_enabled is True

    def test_enabling_google_disables_password(self, settings_factory):
        """開了 Google，帳密自動關閉——這是 issue #32 的核心效果。"""
        s = settings_factory(google="true")
        assert s.GOOGLE_LOGIN_ENABLED is True
        assert s.password_login_enabled is False

    def test_disabling_google_restores_password(self, settings_factory):
        """關掉 Google，帳密自動回來，不會變成沒有任何登入方式。"""
        s = settings_factory(google="false")
        assert s.password_login_enabled is True


class TestEscapeHatch:
    """明確設定永遠優先於連動——Google 出狀況時的後路。"""

    def test_explicit_true_keeps_password_alive(self, settings_factory):
        """這是逃生門本身：Google 開著也要能用帳密登入。"""
        s = settings_factory(google="true", password="true")
        assert s.GOOGLE_LOGIN_ENABLED is True
        assert s.password_login_enabled is True

    def test_explicit_false_with_google_on(self, settings_factory):
        s = settings_factory(google="true", password="false")
        assert s.password_login_enabled is False

    def test_explicit_false_with_google_off(self, settings_factory):
        """兩個都關是合法但危險的組合：後台完全進不去。

        程式不阻止，因為可能是刻意要暫時封鎖後台；前端會顯示
        「目前沒有可用的登入方式」而不是留一片空白。
        """
        s = settings_factory(google="false", password="false")
        assert s.password_login_enabled is False


class TestDefaults:
    def test_google_login_defaults_off(self, settings_factory):
        """預設關閉。程式無從得知主控台有沒有啟用 Google 供應商，
        預設開啟會讓前台出現一顆按下去只會噴錯的按鈕。"""
        s = settings_factory()
        assert s.GOOGLE_LOGIN_ENABLED is False

    def test_admin_accounts_defaults_empty(self, settings_factory):
        """留空＝不檢查。這是為了不讓既有部署更新後突然登不進去，
        但那等於沒有白名單，auth.is_allowed() 會每次印警告。"""
        s = settings_factory()
        assert s.ADMIN_ACCOUNTS == ""
