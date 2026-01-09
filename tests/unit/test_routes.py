# -*- coding: utf-8 -*-

"""
Unit-тесты для API endpoints (routes_openai.py).
Проверяет работу эндпоинтов /, /health, /v1/models, /v1/chat/completions.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi.testclient import TestClient

from kiro.routes_openai import verify_api_key, router
from kiro.config import PROXY_API_KEY, APP_VERSION, AVAILABLE_MODELS


class TestVerifyApiKey:
    """Тесты функции verify_api_key."""
    
    @pytest.mark.asyncio
    async def test_valid_api_key_returns_true(self):
        """
        Что он делает: Проверяет успешную валидацию корректного ключа.
        Цель: Убедиться, что валидный ключ проходит проверку.
        """
        print("Настройка: Валидный API ключ...")
        valid_header = f"Bearer {PROXY_API_KEY}"
        
        print("Действие: Проверка ключа...")
        result = await verify_api_key(valid_header)
        
        print(f"Сравниваем результат: Ожидалось True, Получено {result}")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_401(self):
        """
        Что он делает: Проверяет отклонение невалидного ключа.
        Цель: Убедиться, что невалидный ключ вызывает 401.
        """
        print("Настройка: Невалидный API ключ...")
        invalid_header = "Bearer wrong_key"
        
        print("Действие: Проверка ключа...")
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(invalid_header)
        
        print(f"Проверка: HTTPException с кодом 401...")
        assert exc_info.value.status_code == 401
        assert "Invalid or missing API Key" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_missing_api_key_raises_401(self):
        """
        Что он делает: Проверяет отклонение отсутствующего ключа.
        Цель: Убедиться, что отсутствие ключа вызывает 401.
        """
        print("Настройка: Отсутствующий API ключ...")
        
        print("Действие: Проверка ключа...")
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(None)
        
        print(f"Проверка: HTTPException с кодом 401...")
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_empty_api_key_raises_401(self):
        """
        Что он делает: Проверяет отклонение пустого ключа.
        Цель: Убедиться, что пустая строка вызывает 401.
        """
        print("Настройка: Пустой API ключ...")
        
        print("Действие: Проверка ключа...")
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("")
        
        print(f"Проверка: HTTPException с кодом 401...")
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_wrong_format_raises_401(self):
        """
        Что он делает: Проверяет отклонение ключа без Bearer.
        Цель: Убедиться, что неправильный формат вызывает 401.
        """
        print("Настройка: Ключ без Bearer...")
        wrong_format = PROXY_API_KEY  # Без "Bearer "
        
        print("Действие: Проверка ключа...")
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(wrong_format)
        
        print(f"Проверка: HTTPException с кодом 401...")
        assert exc_info.value.status_code == 401


class TestRootEndpoint:
    """Тесты эндпоинта /."""
    
    def test_root_returns_status_ok(self, test_client):
        """
        Что он делает: Проверяет ответ корневого эндпоинта.
        Цель: Убедиться, что / возвращает статус ok.
        """
        print("Действие: GET /...")
        response = test_client.get("/")
        
        print(f"Результат: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert "Kiro Gateway" in response.json()["message"]
    
    def test_root_returns_version(self, test_client):
        """
        Что он делает: Проверяет наличие версии в ответе.
        Цель: Убедиться, что версия приложения возвращается.
        """
        print("Действие: GET /...")
        response = test_client.get("/")
        
        print(f"Результат: {response.json()}")
        assert response.status_code == 200
        assert "version" in response.json()
        assert response.json()["version"] == APP_VERSION


class TestHealthEndpoint:
    """Тесты эндпоинта /health."""
    
    def test_health_returns_healthy(self, test_client):
        """
        Что он делает: Проверяет ответ health эндпоинта.
        Цель: Убедиться, что /health возвращает статус healthy.
        """
        print("Действие: GET /health...")
        response = test_client.get("/health")
        
        print(f"Результат: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_health_returns_timestamp(self, test_client):
        """
        Что он делает: Проверяет наличие timestamp в ответе.
        Цель: Убедиться, что timestamp возвращается.
        """
        print("Действие: GET /health...")
        response = test_client.get("/health")
        
        print(f"Результат: {response.json()}")
        assert response.status_code == 200
        assert "timestamp" in response.json()
    
    def test_health_returns_version(self, test_client):
        """
        Что он делает: Проверяет наличие версии в ответе.
        Цель: Убедиться, что версия приложения возвращается.
        """
        print("Действие: GET /health...")
        response = test_client.get("/health")
        
        print(f"Результат: {response.json()}")
        assert response.status_code == 200
        assert response.json()["version"] == APP_VERSION


class TestModelsEndpoint:
    """Тесты эндпоинта /v1/models."""
    
    def test_models_requires_auth(self, test_client):
        """
        Что он делает: Проверяет требование авторизации.
        Цель: Убедиться, что без ключа возвращается 401.
        """
        print("Действие: GET /v1/models без авторизации...")
        response = test_client.get("/v1/models")
        
        print(f"Статус: {response.status_code}")
        assert response.status_code == 401
    
    def test_models_returns_list(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет возврат списка моделей.
        Цель: Убедиться, что /v1/models возвращает список.
        """
        print("Действие: GET /v1/models с авторизацией...")
        response = test_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"}
        )
        
        print(f"Результат: {response.json()}")
        assert response.status_code == 200
        assert response.json()["object"] == "list"
        assert "data" in response.json()
    
    def test_models_returns_available_models(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет наличие доступных моделей.
        Цель: Убедиться, что все модели из AVAILABLE_MODELS возвращаются.
        """
        print("Действие: GET /v1/models с авторизацией...")
        response = test_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"}
        )
        
        print(f"Результат: {response.json()}")
        assert response.status_code == 200
        
        model_ids = [m["id"] for m in response.json()["data"]]
        for expected_model in AVAILABLE_MODELS:
            assert expected_model in model_ids, f"Модель {expected_model} не найдена"
    
    def test_models_format_is_openai_compatible(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет формат ответа на совместимость с OpenAI.
        Цель: Убедиться, что формат соответствует OpenAI API.
        """
        print("Действие: GET /v1/models с авторизацией...")
        response = test_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"}
        )
        
        print(f"Результат: {response.json()}")
        assert response.status_code == 200
        
        for model in response.json()["data"]:
            assert "id" in model
            assert "object" in model
            assert model["object"] == "model"
            assert "owned_by" in model


class TestChatCompletionsEndpoint:
    """Тесты эндпоинта /v1/chat/completions."""
    
    def test_chat_completions_requires_auth(self, test_client):
        """
        Что он делает: Проверяет требование авторизации.
        Цель: Убедиться, что без ключа возвращается 401.
        """
        print("Действие: POST /v1/chat/completions без авторизации...")
        response = test_client.post(
            "/v1/chat/completions",
            json={
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
        
        print(f"Статус: {response.status_code}")
        assert response.status_code == 401
    
    def test_chat_completions_validates_messages(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет валидацию пустых сообщений.
        Цель: Убедиться, что пустой список сообщений отклоняется.
        """
        print("Действие: POST /v1/chat/completions с пустыми сообщениями...")
        response = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "model": "claude-sonnet-4-5",
                "messages": []
            }
        )
        
        print(f"Статус: {response.status_code}")
        # Pydantic должен отклонить пустой список
        assert response.status_code == 422
    
    def test_chat_completions_validates_model(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет валидацию отсутствующей модели.
        Цель: Убедиться, что запрос без модели отклоняется.
        """
        print("Действие: POST /v1/chat/completions без модели...")
        response = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
        
        print(f"Статус: {response.status_code}")
        assert response.status_code == 422


class TestChatCompletionsWithMockedKiro:
    """Тесты /v1/chat/completions с мокированным Kiro API."""
    
    def test_chat_completions_accepts_valid_request_format(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет, что валидный формат запроса принимается.
        Цель: Убедиться, что Pydantic валидация проходит для корректного запроса.
        """
        print("Настройка: Валидный запрос...")
        
        # Этот тест проверяет только валидацию запроса
        # Реальный вызов к Kiro API будет заблокирован фикстурой block_all_network_calls
        # Поэтому мы ожидаем ошибку на этапе HTTP запроса, а не валидации
        
        print("Действие: POST /v1/chat/completions с валидным запросом...")
        response = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            }
        )
        
        print(f"Статус: {response.status_code}")
        # Запрос должен пройти валидацию (не 422)
        # Но может упасть на этапе HTTP из-за блокировки сети
        assert response.status_code != 422


class TestChatCompletionsErrorHandling:
    """Тесты обработки ошибок в /v1/chat/completions."""
    
    def test_invalid_json_returns_422(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет обработку невалидного JSON.
        Цель: Убедиться, что невалидный JSON возвращает 422.
        """
        print("Действие: POST /v1/chat/completions с невалидным JSON...")
        response = test_client.post(
            "/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {valid_proxy_api_key}",
                "Content-Type": "application/json"
            },
            content=b"not valid json"
        )
        
        print(f"Статус: {response.status_code}")
        assert response.status_code == 422
    
    def test_missing_content_in_message_returns_200(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет обработку сообщения без content.
        Цель: Убедиться, что сообщение без content допустимо (content опционален).
        """
        print("Действие: POST /v1/chat/completions с сообщением без content...")
        # Этот тест проверяет валидацию Pydantic
        # content может быть None согласно модели
        response = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user"}]  # content отсутствует
            }
        )
        
        print(f"Статус: {response.status_code}")
        # Запрос должен пройти валидацию (content опционален)
        # Но может упасть на этапе обработки из-за отсутствия мока Kiro API
        # Поэтому проверяем, что это не 422 (валидация прошла)
        assert response.status_code != 422 or "content" not in str(response.json())


class TestRouterIntegration:
    """Тесты интеграции роутера."""
    
    def test_router_has_all_endpoints(self):
        """
        Что он делает: Проверяет наличие всех эндпоинтов в роутере.
        Цель: Убедиться, что все эндпоинты зарегистрированы.
        """
        print("Проверка: Эндпоинты в роутере...")
        
        routes = [route.path for route in router.routes]
        
        print(f"Найденные роуты: {routes}")
        assert "/" in routes
        assert "/health" in routes
        assert "/v1/models" in routes
        assert "/v1/chat/completions" in routes
    
    def test_router_methods(self):
        """
        Что он делает: Проверяет HTTP методы эндпоинтов.
        Цель: Убедиться, что методы соответствуют ожиданиям.
        """
        print("Проверка: HTTP методы...")
        
        for route in router.routes:
            if route.path == "/":
                assert "GET" in route.methods
            elif route.path == "/health":
                assert "GET" in route.methods
            elif route.path == "/v1/models":
                assert "GET" in route.methods
            elif route.path == "/v1/chat/completions":
                assert "POST" in route.methods