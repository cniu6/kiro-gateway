# -*- coding: utf-8 -*-

"""
Integration-тесты для полного end-to-end flow.
Проверяет взаимодействие всех компонентов системы.
"""

import pytest
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient
import httpx

from kiro.config import PROXY_API_KEY, AVAILABLE_MODELS


class TestFullChatCompletionFlow:
    """Integration-тесты полного flow chat completions."""
    
    def test_full_flow_health_to_models_to_chat(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет полный flow от health check до chat completions.
        Цель: Убедиться, что все эндпоинты работают вместе.
        """
        print("Шаг 1: Health check...")
        health_response = test_client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        print(f"Health: {health_response.json()}")
        
        print("Шаг 2: Получение списка моделей...")
        models_response = test_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"}
        )
        assert models_response.status_code == 200
        assert len(models_response.json()["data"]) > 0
        print(f"Модели: {[m['id'] for m in models_response.json()['data']]}")
        
        print("Шаг 3: Валидация запроса chat completions...")
        # Этот запрос пройдёт валидацию, но упадёт на HTTP из-за блокировки сети
        chat_response = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
        # Запрос должен пройти валидацию (не 422)
        assert chat_response.status_code != 422
        print(f"Chat response status: {chat_response.status_code}")
    
    def test_authentication_flow(self, test_client, valid_proxy_api_key, invalid_proxy_api_key):
        """
        Что он делает: Проверяет flow аутентификации.
        Цель: Убедиться, что защищённые эндпоинты требуют авторизации.
        """
        print("Шаг 1: Запрос без авторизации...")
        no_auth_response = test_client.get("/v1/models")
        assert no_auth_response.status_code == 401
        print(f"Без авторизации: {no_auth_response.status_code}")
        
        print("Шаг 2: Запрос с неверным ключом...")
        wrong_auth_response = test_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {invalid_proxy_api_key}"}
        )
        assert wrong_auth_response.status_code == 401
        print(f"Неверный ключ: {wrong_auth_response.status_code}")
        
        print("Шаг 3: Запрос с верным ключом...")
        valid_auth_response = test_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"}
        )
        assert valid_auth_response.status_code == 200
        print(f"Верный ключ: {valid_auth_response.status_code}")
    
    def test_openai_compatibility_format(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет совместимость формата ответов с OpenAI API.
        Цель: Убедиться, что ответы соответствуют спецификации OpenAI.
        """
        print("Проверка формата /v1/models...")
        models_response = test_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"}
        )
        
        assert models_response.status_code == 200
        data = models_response.json()
        
        # Проверяем структуру ответа OpenAI
        assert "object" in data
        assert data["object"] == "list"
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # Проверяем структуру каждой модели
        for model in data["data"]:
            assert "id" in model
            assert "object" in model
            assert model["object"] == "model"
            assert "owned_by" in model
            assert "created" in model
        
        print(f"Формат соответствует OpenAI API: {len(data['data'])} моделей")


class TestRequestValidationFlow:
    """Integration-тесты валидации запросов."""
    
    def test_chat_completions_request_validation(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет валидацию различных форматов запросов.
        Цель: Убедиться, что валидация работает корректно.
        """
        print("Тест 1: Пустые сообщения...")
        empty_messages = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={"model": "claude-sonnet-4-5", "messages": []}
        )
        assert empty_messages.status_code == 422
        print(f"Пустые сообщения: {empty_messages.status_code}")
        
        print("Тест 2: Отсутствует model...")
        no_model = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={"messages": [{"role": "user", "content": "Hello"}]}
        )
        assert no_model.status_code == 422
        print(f"Без model: {no_model.status_code}")
        
        print("Тест 3: Отсутствует messages...")
        no_messages = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={"model": "claude-sonnet-4-5"}
        )
        assert no_messages.status_code == 422
        print(f"Без messages: {no_messages.status_code}")
        
        print("Тест 4: Валидный запрос...")
        valid_request = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
        # Валидация должна пройти (не 422)
        assert valid_request.status_code != 422
        print(f"Валидный запрос: {valid_request.status_code}")
    
    def test_complex_message_formats(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет обработку сложных форматов сообщений.
        Цель: Убедиться, что multimodal и tool форматы принимаются.
        """
        print("Тест 1: System + User сообщения...")
        system_user = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "model": "claude-sonnet-4-5",
                "messages": [
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hello"}
                ]
            }
        )
        assert system_user.status_code != 422
        print(f"System + User: {system_user.status_code}")
        
        print("Тест 2: Multi-turn conversation...")
        multi_turn = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "model": "claude-sonnet-4-5",
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                    {"role": "user", "content": "How are you?"}
                ]
            }
        )
        assert multi_turn.status_code != 422
        print(f"Multi-turn: {multi_turn.status_code}")
        
        print("Тест 3: С tools...")
        with_tools = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user", "content": "What's the weather?"}],
                "tools": [{
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get weather",
                        "parameters": {"type": "object", "properties": {}}
                    }
                }]
            }
        )
        assert with_tools.status_code != 422
        print(f"С tools: {with_tools.status_code}")


class TestErrorHandlingFlow:
    """Integration-тесты обработки ошибок."""
    
    def test_invalid_json_handling(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет обработку невалидного JSON.
        Цель: Убедиться, что невалидный JSON возвращает понятную ошибку.
        """
        print("Отправка невалидного JSON...")
        response = test_client.post(
            "/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {valid_proxy_api_key}",
                "Content-Type": "application/json"
            },
            content=b"not valid json"
        )
        
        assert response.status_code == 422
        print(f"Невалидный JSON: {response.status_code}")
    
    def test_wrong_content_type_handling(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет обработку неверного Content-Type.
        Цель: Убедиться, что неверный Content-Type обрабатывается.
        """
        print("Отправка с неверным Content-Type...")
        response = test_client.post(
            "/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {valid_proxy_api_key}",
                "Content-Type": "text/plain"
            },
            content=b"Hello"
        )
        
        # Должна быть ошибка валидации
        assert response.status_code == 422
        print(f"Неверный Content-Type: {response.status_code}")


class TestModelsEndpointIntegration:
    """Integration-тесты эндпоинта /v1/models."""
    
    def test_models_returns_all_available_models(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет, что все модели из конфига возвращаются.
        Цель: Убедиться в полноте списка моделей.
        """
        print("Получение списка моделей...")
        response = test_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"}
        )
        
        assert response.status_code == 200
        
        returned_ids = {m["id"] for m in response.json()["data"]}
        expected_ids = set(AVAILABLE_MODELS)
        
        print(f"Возвращённые модели: {returned_ids}")
        print(f"Ожидаемые модели: {expected_ids}")
        
        assert returned_ids == expected_ids
    
    def test_models_caching_behavior(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет поведение кэширования моделей.
        Цель: Убедиться, что повторные запросы работают корректно.
        """
        print("Первый запрос моделей...")
        response1 = test_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"}
        )
        assert response1.status_code == 200
        
        print("Второй запрос моделей...")
        response2 = test_client.get(
            "/v1/models",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"}
        )
        assert response2.status_code == 200
        
        # Ответы должны быть идентичны
        assert response1.json()["data"] == response2.json()["data"]
        print("Кэширование работает корректно")


class TestStreamingFlagHandling:
    """Integration-тесты обработки флага stream."""
    
    def test_stream_true_accepted(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет, что stream=true принимается.
        Цель: Убедиться, что streaming режим доступен.
        
        Примечание: Для streaming режима нужен мок HTTP клиента,
        так как запрос выполняется внутри генератора.
        """
        print("Запрос с stream=true...")
        
        # Создаём мок response для streaming
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        async def mock_aiter_bytes():
            yield b'{"content":"Hello"}'
            yield b'{"usage":0.5}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        mock_response.aclose = AsyncMock()
        
        # Мокируем request_with_retry чтобы вернуть наш мок response
        with patch('kiro.routes_openai.KiroHttpClient') as MockHttpClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.request_with_retry = AsyncMock(return_value=mock_response)
            mock_client_instance.client = AsyncMock()
            mock_client_instance.close = AsyncMock()
            MockHttpClient.return_value = mock_client_instance
            
            response = test_client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
                json={
                    "model": "claude-sonnet-4-5",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": True
                }
            )
        
        # Валидация должна пройти и streaming должен работать
        assert response.status_code == 200
        print(f"stream=true: {response.status_code}")
    
    def test_stream_false_accepted(self, test_client, valid_proxy_api_key):
        """
        Что он делает: Проверяет, что stream=false принимается.
        Цель: Убедиться, что non-streaming режим доступен.
        """
        print("Запрос с stream=false...")
        response = test_client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {valid_proxy_api_key}"},
            json={
                "model": "claude-sonnet-4-5",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            }
        )
        
        # Валидация должна пройти
        assert response.status_code != 422
        print(f"stream=false: {response.status_code}")


class TestHealthEndpointIntegration:
    """Integration-тесты health endpoints."""
    
    def test_root_and_health_consistency(self, test_client):
        """
        Что он делает: Проверяет консистентность / и /health.
        Цель: Убедиться, что оба эндпоинта возвращают корректный статус.
        """
        print("Запрос к /...")
        root_response = test_client.get("/")
        
        print("Запрос к /health...")
        health_response = test_client.get("/health")
        
        assert root_response.status_code == 200
        assert health_response.status_code == 200
        
        # Оба должны показывать "ok" статус
        assert root_response.json()["status"] == "ok"
        assert health_response.json()["status"] == "healthy"
        
        # Версии должны совпадать
        assert root_response.json()["version"] == health_response.json()["version"]
        
        print("Health endpoints консистентны")
