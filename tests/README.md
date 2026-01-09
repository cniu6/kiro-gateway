# Tests for Kiro Gateway

A comprehensive set of unit and integration tests for Kiro Gateway, providing full coverage of all system components.

## Testing Philosophy: Complete Network Isolation

**The key principle of this test suite is 100% isolation from real network requests.**

This is achieved through a global, automatically applied fixture `block_all_network_calls` in `tests/conftest.py`. It intercepts and blocks any attempts by `httpx.AsyncClient` to establish connections at the application level.

**Benefits:**
1.  **Reliability**: Tests don't depend on external API availability or network state.
2.  **Speed**: Absence of real network delays makes test execution instant.
3.  **Security**: Guarantees that test runs never use real credentials.

Any attempt to make an unauthorized network call will result in immediate test failure with an error, ensuring strict isolation control.

## Running Tests

### Installing Dependencies

```bash
# Main project dependencies
pip install -r requirements.txt

# Additional testing dependencies
pip install pytest pytest-asyncio hypothesis
```

### Running All Tests

```bash
# Run the entire test suite
pytest

# Run with verbose output
pytest -v

# Run with verbose output and coverage
pytest -v -s --tb=short

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run a specific file
pytest tests/unit/test_auth_manager.py -v

# Run a specific test
pytest tests/unit/test_auth_manager.py::TestKiroAuthManagerInitialization::test_initialization_stores_credentials -v
```

### pytest Options

```bash
# Stop on first failure
pytest -x

# Show local variables on errors
pytest -l

# Run in parallel mode (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

## Test Structure

```
tests/
├── conftest.py                      # Shared fixtures and utilities
├── unit/                            # Unit tests for individual components
│   ├── test_auth_manager.py        # KiroAuthManager tests
│   ├── test_cache.py               # ModelInfoCache tests
│   ├── test_config.py              # Configuration tests (SERVER_HOST, SERVER_PORT, LOG_LEVEL, etc.)
│   ├── test_converters_anthropic.py # Anthropic Messages API → Kiro converter tests
│   ├── test_converters_core.py     # Shared conversion logic tests (UnifiedMessage, merging, etc.)
│   ├── test_converters_openai.py   # OpenAI Chat API → Kiro converter tests
│   ├── test_debug_logger.py        # DebugLogger tests (off/errors/all modes)
│   ├── test_main_cli.py            # CLI argument parsing tests (--host, --port)
│   ├── test_parsers.py             # AwsEventStreamParser tests
│   ├── test_routes_anthropic.py    # Anthropic API endpoint tests (/v1/messages)
│   ├── test_routes_openai.py       # OpenAI API endpoint tests (/v1/chat/completions)
│   ├── test_streaming_anthropic.py # Anthropic streaming response tests
│   ├── test_streaming_core.py      # Shared streaming logic tests
│   ├── test_streaming_openai.py    # OpenAI streaming response tests
│   ├── test_thinking_parser.py     # ThinkingParser tests (FSM for thinking blocks)
│   ├── test_tokenizer.py           # Tokenizer tests (tiktoken)
│   └── test_http_client.py         # KiroHttpClient tests
├── integration/                     # Integration tests for full flow
│   └── test_full_flow.py           # End-to-end tests
└── README.md                        # This file
```

## Test Coverage

### `conftest.py`

Shared fixtures and utilities for all tests:

**Environment Fixtures:**
- **`mock_env_vars()`**: Mocks environment variables (REFRESH_TOKEN, PROXY_API_KEY)
  - **What it does**: Isolates tests from real credentials
  - **Purpose**: Security and test reproducibility

**Data Fixtures:**
- **`valid_kiro_token()`**: Returns a mock Kiro access token
  - **What it does**: Provides a predictable token for tests
  - **Purpose**: Testing without real Kiro requests

- **`mock_kiro_token_response()`**: Factory for creating mock refreshToken responses
  - **What it does**: Generates Kiro auth endpoint response structure
  - **Purpose**: Testing various token refresh scenarios

- **`temp_creds_file()`**: Creates a temporary JSON file with credentials (Kiro Desktop format)
  - **What it does**: Provides a file for testing credentials loading
  - **Purpose**: Testing credentials file operations

- **`temp_aws_sso_creds_file()`**: Creates a temporary JSON file with AWS SSO OIDC credentials
  - **What it does**: Provides a file with clientId and clientSecret for testing AWS SSO auth
  - **Purpose**: Testing AWS SSO OIDC credentials loading

- **`temp_sqlite_db()`**: Creates a temporary SQLite database (kiro-cli format)
  - **What it does**: Provides a database with auth_kv table for testing SQLite loading
  - **Purpose**: Testing kiro-cli SQLite credentials loading

- **`temp_sqlite_db_token_only()`**: Creates SQLite database with token only (no device-registration)
  - **What it does**: Provides a partial database for testing error handling
  - **Purpose**: Testing partial SQLite data loading

- **`temp_sqlite_db_invalid_json()`**: Creates SQLite database with invalid JSON
  - **What it does**: Provides a database with corrupted data for testing error handling
  - **Purpose**: Testing JSON decode error handling

- **`mock_aws_sso_oidc_token_response()`**: Factory for creating mock AWS SSO OIDC token responses
  - **What it does**: Generates AWS SSO OIDC token endpoint response structure
  - **Purpose**: Testing various AWS SSO OIDC token refresh scenarios

- **`sample_openai_chat_request()`**: Factory for creating OpenAI requests
  - **What it does**: Generates valid chat completion requests
  - **Purpose**: Convenient creation of test requests with different parameters

**Security Fixtures:**
- **`valid_proxy_api_key()`**: Valid proxy API key
- **`invalid_proxy_api_key()`**: Invalid key for negative tests
- **`auth_headers()`**: Factory for creating Authorization headers

**HTTP Fixtures:**
- **`mock_httpx_client()`**: Mocked httpx.AsyncClient
  - **What it does**: Isolates tests from real HTTP requests
  - **Purpose**: Test speed and reliability

- **`mock_httpx_response()`**: Factory for creating mock HTTP responses
  - **What it does**: Creates configurable httpx.Response objects
  - **Purpose**: Testing various HTTP scenarios

**Application Fixtures:**
- **`clean_app()`**: Clean FastAPI app instance
  - **What it does**: Returns a "clean" application instance
  - **Purpose**: Ensure application state isolation between tests

- **`test_client()`**: Synchronous FastAPI TestClient
- **`async_test_client()`**: Asynchronous test client for async endpoints

---

### `tests/unit/test_auth_manager.py`

Unit tests for **KiroAuthManager** (Kiro token management).

#### `TestKiroAuthManagerInitialization`

- **`test_initialization_stores_credentials()`**:
  - **What it does**: Verifies correct credential storage during creation
  - **Purpose**: Ensure all constructor parameters are stored in private fields

- **`test_initialization_sets_correct_urls_for_region()`**:
  - **What it does**: Verifies URL formation based on region
  - **Purpose**: Ensure URLs are dynamically formed with the correct region

- **`test_initialization_generates_fingerprint()`**:
  - **What it does**: Verifies unique fingerprint generation
  - **Purpose**: Ensure fingerprint is generated and has correct format

#### `TestKiroAuthManagerCredentialsFile`

- **`test_load_credentials_from_file()`**:
  - **What it does**: Verifies credentials loading from JSON file
  - **Purpose**: Ensure data is correctly read from file

- **`test_load_credentials_file_not_found()`**:
  - **What it does**: Verifies handling of missing credentials file
  - **Purpose**: Ensure application doesn't crash when file is missing

#### `TestKiroAuthManagerTokenExpiration`

- **`test_is_token_expiring_soon_returns_true_when_no_expires_at()`**:
  - **What it does**: Verifies that without expires_at, token is considered expiring
  - **Purpose**: Ensure safe behavior when time information is missing

- **`test_is_token_expiring_soon_returns_true_when_expired()`**:
  - **What it does**: Verifies that expired token is correctly identified
  - **Purpose**: Ensure token in the past is considered expiring

- **`test_is_token_expiring_soon_returns_true_within_threshold()`**:
  - **What it does**: Verifies that token within threshold is considered expiring
  - **Purpose**: Ensure token is refreshed in advance (10 minutes before expiration)

- **`test_is_token_expiring_soon_returns_false_when_valid()`**:
  - **What it does**: Verifies that valid token is not considered expiring
  - **Purpose**: Ensure token far in the future doesn't require refresh

#### `TestKiroAuthManagerTokenRefresh`

- **`test_refresh_token_successful()`**:
  - **What it does**: Tests successful token refresh via Kiro API
  - **Purpose**: Verify correct setting of access_token and expires_at

- **`test_refresh_token_updates_refresh_token()`**:
  - **What it does**: Verifies refresh_token update from response
  - **Purpose**: Ensure new refresh_token is saved

- **`test_refresh_token_missing_access_token_raises()`**:
  - **What it does**: Verifies handling of response without accessToken
  - **Purpose**: Ensure exception is thrown for incorrect response

- **`test_refresh_token_no_refresh_token_raises()`**:
  - **What it does**: Verifies handling of missing refresh_token
  - **Purpose**: Ensure exception is thrown without refresh_token

#### `TestKiroAuthManagerGetAccessToken`

- **`test_get_access_token_refreshes_when_expired()`**:
  - **What it does**: Verifies automatic refresh of expired token
  - **Purpose**: Ensure stale token is refreshed before return

- **`test_get_access_token_returns_valid_without_refresh()`**:
  - **What it does**: Verifies return of valid token without extra requests
  - **Purpose**: Optimization - don't make requests if token is still valid

- **`test_get_access_token_thread_safety()`**:
  - **What it does**: Verifies thread safety via asyncio.Lock
  - **Purpose**: Prevent race conditions during parallel calls

#### `TestKiroAuthManagerForceRefresh`

- **`test_force_refresh_updates_token()`**:
  - **What it does**: Verifies forced token refresh
  - **Purpose**: Ensure force_refresh always refreshes token

#### `TestKiroAuthManagerProperties`

- **`test_profile_arn_property()`**:
  - **What it does**: Verifies profile_arn property
  - **Purpose**: Ensure profile_arn is accessible via property

- **`test_region_property()`**:
  - **What it does**: Verifies region property
  - **Purpose**: Ensure region is accessible via property

- **`test_api_host_property()`**:
  - **What it does**: Verifies api_host property
  - **Purpose**: Ensure api_host is formed correctly

- **`test_fingerprint_property()`**:
  - **What it does**: Verifies fingerprint property
  - **Purpose**: Ensure fingerprint is accessible via property

#### `TestAuthTypeEnum`

Tests for AuthType enum (AWS SSO OIDC support).

- **`test_auth_type_enum_values()`**:
  - **What it does**: Verifies AuthType enum contains KIRO_DESKTOP and AWS_SSO_OIDC
  - **Purpose**: Ensure enum values are correctly defined

#### `TestKiroAuthManagerDetectAuthType`

Tests for `_detect_auth_type()` method.

- **`test_detect_auth_type_kiro_desktop_when_no_client_credentials()`**:
  - **What it does**: Verifies KIRO_DESKTOP is detected without clientId/clientSecret
  - **Purpose**: Ensure default auth type is KIRO_DESKTOP

- **`test_detect_auth_type_aws_sso_oidc_when_client_credentials_present()`**:
  - **What it does**: Verifies AWS_SSO_OIDC is detected with clientId and clientSecret
  - **Purpose**: Ensure AWS SSO OIDC is auto-detected from credentials

- **`test_detect_auth_type_kiro_desktop_when_only_client_id()`**:
  - **What it does**: Verifies KIRO_DESKTOP when only clientId is present
  - **Purpose**: Ensure both clientId AND clientSecret are required for AWS SSO OIDC

- **`test_detect_auth_type_kiro_desktop_when_only_client_secret()`**:
  - **What it does**: Verifies KIRO_DESKTOP when only clientSecret is present
  - **Purpose**: Ensure both clientId AND clientSecret are required for AWS SSO OIDC

#### `TestKiroAuthManagerAwsSsoCredentialsFile`

Tests for loading AWS SSO OIDC credentials from JSON file.

- **`test_load_credentials_from_file_with_client_id_and_secret()`**:
  - **What it does**: Verifies clientId and clientSecret are loaded from JSON file
  - **Purpose**: Ensure AWS SSO fields are correctly read from file

- **`test_load_credentials_from_file_auto_detects_aws_sso_oidc()`**:
  - **What it does**: Verifies auth_type is auto-detected as AWS_SSO_OIDC after loading
  - **Purpose**: Ensure auth type is automatically determined from file contents

- **`test_load_kiro_desktop_file_stays_kiro_desktop()`**:
  - **What it does**: Verifies Kiro Desktop file doesn't change auth type to AWS SSO
  - **Purpose**: Ensure file without clientId/clientSecret stays KIRO_DESKTOP

#### `TestKiroAuthManagerSqliteCredentials`

Tests for loading credentials from SQLite database (kiro-cli format).

- **`test_load_credentials_from_sqlite_success()`**:
  - **What it does**: Verifies successful credentials loading from SQLite
  - **Purpose**: Ensure all data is correctly read from database

- **`test_load_credentials_from_sqlite_file_not_found()`**:
  - **What it does**: Verifies handling of missing SQLite file
  - **Purpose**: Ensure application doesn't crash when file is missing

- **`test_load_credentials_from_sqlite_loads_token_data()`**:
  - **What it does**: Verifies token data loading from SQLite
  - **Purpose**: Ensure access_token, refresh_token, sso_region are loaded (API region stays at us-east-1)

- **`test_load_credentials_from_sqlite_loads_device_registration()`**:
  - **What it does**: Verifies device registration loading from SQLite
  - **Purpose**: Ensure client_id and client_secret are loaded

- **`test_load_credentials_from_sqlite_auto_detects_aws_sso_oidc()`**:
  - **What it does**: Verifies auth_type is auto-detected as AWS_SSO_OIDC after loading
  - **Purpose**: Ensure auth type is automatically determined from SQLite contents

- **`test_load_credentials_from_sqlite_handles_missing_registration_key()`**:
  - **What it does**: Verifies handling of missing device-registration key
  - **Purpose**: Ensure application doesn't crash without device-registration

- **`test_load_credentials_from_sqlite_handles_invalid_json()`**:
  - **What it does**: Verifies handling of invalid JSON in SQLite
  - **Purpose**: Ensure application doesn't crash with invalid JSON

- **`test_sqlite_takes_priority_over_json_file()`**:
  - **What it does**: Verifies SQLite takes priority over JSON file
  - **Purpose**: Ensure SQLite is loaded instead of JSON when both are specified (checks sso_region, not api_region)

#### `TestKiroAuthManagerRefreshTokenRouting`

Tests for `_refresh_token_request()` routing based on auth_type.

- **`test_refresh_token_request_routes_to_kiro_desktop()`**:
  - **What it does**: Verifies KIRO_DESKTOP calls _refresh_token_kiro_desktop
  - **Purpose**: Ensure correct routing for Kiro Desktop auth

- **`test_refresh_token_request_routes_to_aws_sso_oidc()`**:
  - **What it does**: Verifies AWS_SSO_OIDC calls _refresh_token_aws_sso_oidc
  - **Purpose**: Ensure correct routing for AWS SSO OIDC auth

#### `TestKiroAuthManagerAwsSsoOidcRefresh`

Tests for `_refresh_token_aws_sso_oidc()` method.

- **`test_refresh_token_aws_sso_oidc_success()`**:
  - **What it does**: Tests successful token refresh via AWS SSO OIDC
  - **Purpose**: Verify access_token and expires_at are set on success

- **`test_refresh_token_aws_sso_oidc_raises_without_refresh_token()`**:
  - **What it does**: Verifies ValueError is raised without refresh_token
  - **Purpose**: Ensure exception is thrown without refresh_token

- **`test_refresh_token_aws_sso_oidc_raises_without_client_id()`**:
  - **What it does**: Verifies ValueError is raised without client_id
  - **Purpose**: Ensure exception is thrown without client_id

- **`test_refresh_token_aws_sso_oidc_raises_without_client_secret()`**:
  - **What it does**: Verifies ValueError is raised without client_secret
  - **Purpose**: Ensure exception is thrown without client_secret

- **`test_refresh_token_aws_sso_oidc_uses_correct_endpoint()`**:
  - **What it does**: Verifies correct endpoint is used
  - **Purpose**: Ensure request goes to https://oidc.{region}.amazonaws.com/token

- **`test_refresh_token_aws_sso_oidc_uses_form_urlencoded()`**:
  - **What it does**: Verifies form-urlencoded format is used
  - **Purpose**: Ensure Content-Type = application/x-www-form-urlencoded

- **`test_refresh_token_aws_sso_oidc_sends_correct_grant_type()`**:
  - **What it does**: Verifies correct grant_type is sent
  - **Purpose**: Ensure grant_type=refresh_token

- **`test_refresh_token_aws_sso_oidc_updates_tokens()`**:
  - **What it does**: Verifies access_token and refresh_token are updated
  - **Purpose**: Ensure both tokens are updated from response

- **`test_refresh_token_aws_sso_oidc_calculates_expiration()`**:
  - **What it does**: Verifies expiration time is calculated correctly
  - **Purpose**: Ensure expires_at is calculated based on expiresIn

- **`test_refresh_token_aws_sso_oidc_does_not_send_scopes()`**:
  - **What it does**: Verifies that scopes are NOT sent in refresh request even when loaded from SQLite
  - **Purpose**: Per OAuth 2.0 RFC 6749 Section 6, scope is optional in refresh and AWS SSO OIDC returns invalid_request if scope is sent (fix for issue #12 with @mzazon)

- **`test_refresh_token_aws_sso_oidc_works_without_scopes()`**:
  - **What it does**: Verifies refresh works when scopes are None
  - **Purpose**: Ensure backward compatibility with credentials that don't have scopes (JSON file users like @uratmangun)

#### `TestKiroAuthManagerAuthTypeProperty`

Tests for auth_type property and constructor with new parameters.

- **`test_auth_type_property_returns_correct_value()`**:
  - **What it does**: Verifies auth_type property returns correct value
  - **Purpose**: Ensure property works correctly

- **`test_init_with_client_id_and_secret()`**:
  - **What it does**: Verifies initialization with client_id and client_secret
  - **Purpose**: Ensure parameters are stored in private fields

- **`test_init_with_sqlite_db_parameter()`**:
  - **What it does**: Verifies initialization with sqlite_db parameter
  - **Purpose**: Ensure data is loaded from SQLite

#### `TestKiroAuthManagerSsoRegionSeparation`

Tests for SSO region separation from API region (Issue #16 fix).

Background: CodeWhisperer API only exists in us-east-1, but users may have SSO credentials from other regions (e.g., ap-southeast-1 for Singapore). The fix separates SSO region (for OIDC token refresh) from API region.

- **`test_api_region_stays_us_east_1_when_loading_from_sqlite()`**:
  - **What it does**: Verifies API region doesn't change when loading from SQLite
  - **Purpose**: Ensure CodeWhisperer API calls go to us-east-1 regardless of SSO region

- **`test_sso_region_stored_separately_from_api_region()`**:
  - **What it does**: Verifies SSO region is stored in _sso_region field
  - **Purpose**: Ensure SSO region is available for OIDC token refresh

- **`test_sso_region_none_when_not_loaded_from_sqlite()`**:
  - **What it does**: Verifies _sso_region is None when not loading from SQLite
  - **Purpose**: Ensure backward compatibility with direct credential initialization

- **`test_oidc_refresh_uses_sso_region()`**:
  - **What it does**: Verifies OIDC token refresh uses SSO region, not API region
  - **Purpose**: Ensure token refresh goes to correct regional OIDC endpoint (e.g., ap-southeast-1)

- **`test_oidc_refresh_falls_back_to_api_region_when_no_sso_region()`**:
  - **What it does**: Verifies OIDC refresh uses API region when SSO region not set
  - **Purpose**: Ensure backward compatibility when _sso_region is None

- **`test_api_hosts_not_updated_when_loading_from_sqlite()`**:
  - **What it does**: Verifies API hosts don't change when loading from SQLite
  - **Purpose**: Ensure all API calls go to us-east-1 where CodeWhisperer exists

**New tests for "try first, reload on failure" pattern (PR #22 fix):**

Background: AWS SSO OIDC refresh tokens are one-time use. When you get a new token, the old one is invalidated. The original PR #22 proposed always reloading from SQLite before refresh, but this would break when the container successfully refreshes its own token (the old token in SQLite would overwrite the valid in-memory token). The fix implements "try first, reload on failure" pattern - use in-memory token first, only reload from SQLite on 400 error.

- **`test_refresh_token_aws_sso_oidc_uses_memory_token_first()`**:
  - **What it does**: Verifies that in-memory token is used first, not SQLite
  - **Purpose**: Ensure container's successfully refreshed token is used (not overwritten by SQLite)

- **`test_refresh_token_aws_sso_oidc_reloads_sqlite_on_400_error()`**:
  - **What it does**: Verifies SQLite is reloaded and retry happens on 400 error
  - **Purpose**: Pick up fresh tokens after kiro-cli re-login when in-memory token is stale

- **`test_refresh_token_aws_sso_oidc_no_retry_on_non_400_error()`**:
  - **What it does**: Verifies that non-400 errors are not retried
  - **Purpose**: Ensure only 400 (invalid_request) triggers SQLite reload

- **`test_refresh_token_aws_sso_oidc_no_retry_without_sqlite_db()`**:
  - **What it does**: Verifies that 400 error is not retried when sqlite_db is not set
  - **Purpose**: Ensure retry only happens when SQLite source is available

---

### `tests/unit/test_cache.py`

Unit tests for **ModelInfoCache** (model metadata cache). **23 tests.**

#### `TestModelInfoCacheInitialization`

- **`test_initialization_creates_empty_cache()`**:
  - **What it does**: Verifies that cache is created empty
  - **Purpose**: Ensure correct initialization

- **`test_initialization_with_custom_ttl()`**:
  - **What it does**: Verifies cache creation with custom TTL
  - **Purpose**: Ensure TTL can be configured

- **`test_initialization_last_update_is_none()`**:
  - **What it does**: Verifies that last_update_time is initially None
  - **Purpose**: Ensure update time is not set before first update

#### `TestModelInfoCacheUpdate`

- **`test_update_populates_cache()`**:
  - **What it does**: Verifies cache population with data
  - **Purpose**: Ensure update() correctly saves models

- **`test_update_sets_last_update_time()`**:
  - **What it does**: Verifies setting of last update time
  - **Purpose**: Ensure last_update_time is set after update

- **`test_update_replaces_existing_data()`**:
  - **What it does**: Verifies data replacement on repeated update
  - **Purpose**: Ensure old data is completely replaced

- **`test_update_with_empty_list()`**:
  - **What it does**: Verifies update with empty list
  - **Purpose**: Ensure cache is cleared on empty update

#### `TestModelInfoCacheGet`

- **`test_get_returns_model_info()`**:
  - **What it does**: Verifies retrieval of model information
  - **Purpose**: Ensure get() returns correct data

- **`test_get_returns_none_for_unknown_model()`**:
  - **What it does**: Verifies None return for unknown model
  - **Purpose**: Ensure get() doesn't crash when model is missing

- **`test_get_from_empty_cache()`**:
  - **What it does**: Verifies get() from empty cache
  - **Purpose**: Ensure empty cache doesn't cause errors

#### `TestModelInfoCacheGetMaxInputTokens`

- **`test_get_max_input_tokens_returns_value()`**:
  - **What it does**: Verifies retrieval of maxInputTokens for model
  - **Purpose**: Ensure value is extracted from tokenLimits

- **`test_get_max_input_tokens_returns_default_for_unknown()`**:
  - **What it does**: Verifies default return for unknown model
  - **Purpose**: Ensure DEFAULT_MAX_INPUT_TOKENS is returned

- **`test_get_max_input_tokens_returns_default_when_no_token_limits()`**:
  - **What it does**: Verifies default return when tokenLimits is missing
  - **Purpose**: Ensure model without tokenLimits doesn't break logic

- **`test_get_max_input_tokens_returns_default_when_max_input_is_none()`**:
  - **What it does**: Verifies default return when maxInputTokens=None
  - **Purpose**: Ensure None in tokenLimits is handled correctly

#### `TestModelInfoCacheIsEmpty` and `TestModelInfoCacheIsStale`

- **`test_is_empty_returns_true_for_new_cache()`**: Verifies is_empty() for new cache
- **`test_is_empty_returns_false_after_update()`**: Verifies is_empty() after population
- **`test_is_stale_returns_true_for_new_cache()`**: Verifies is_stale() for new cache
- **`test_is_stale_returns_false_after_recent_update()`**: Verifies is_stale() right after update
- **`test_is_stale_returns_true_after_ttl_expires()`**: Verifies is_stale() after TTL expiration

#### `TestModelInfoCacheGetAllModelIds`

- **`test_get_all_model_ids_returns_empty_for_new_cache()`**: Verifies get_all_model_ids() for empty cache
- **`test_get_all_model_ids_returns_all_ids()`**: Verifies get_all_model_ids() for populated cache

#### `TestModelInfoCacheThreadSafety`

- **`test_concurrent_updates_dont_corrupt_cache()`**:
  - **What it does**: Verifies thread safety during parallel updates
  - **Purpose**: Ensure asyncio.Lock protects against race conditions

- **`test_concurrent_reads_are_safe()`**:
  - **What it does**: Verifies safety of parallel reads
  - **Purpose**: Ensure multiple get() calls don't cause issues

---

### `tests/unit/test_config.py`

Unit tests for **configuration module** (loading settings from environment variables). **21 tests.**

#### `TestServerHostConfig`

Tests for SERVER_HOST configuration.

- **`test_default_server_host_is_0_0_0_0()`**:
  - **What it does**: Verifies that SERVER_HOST defaults to 0.0.0.0
  - **Purpose**: Ensure that 0.0.0.0 (all interfaces) is used when no environment variable is set

- **`test_server_host_from_environment()`**:
  - **What it does**: Verifies loading SERVER_HOST from environment variable
  - **Purpose**: Ensure that the value from environment is used

- **`test_server_host_custom_value()`**:
  - **What it does**: Verifies setting SERVER_HOST to a custom IP address
  - **Purpose**: Ensure that any valid IP address can be used

#### `TestServerPortConfig`

Tests for SERVER_PORT configuration.

- **`test_default_server_port_is_8000()`**:
  - **What it does**: Verifies that SERVER_PORT defaults to 8000
  - **Purpose**: Ensure that 8000 is used when no environment variable is set

- **`test_server_port_from_environment()`**:
  - **What it does**: Verifies loading SERVER_PORT from environment variable
  - **Purpose**: Ensure that the value from environment is used

- **`test_server_port_custom_value()`**:
  - **What it does**: Verifies setting SERVER_PORT to a custom port number
  - **Purpose**: Ensure that any valid port number can be used

- **`test_server_port_is_integer()`**:
  - **What it does**: Verifies that SERVER_PORT is converted to integer
  - **Purpose**: Ensure that string from environment is converted to int

#### `TestLogLevelConfig`

Tests for LOG_LEVEL configuration.

- **`test_default_log_level_is_info()`**:
  - **What it does**: Verifies that default LOG_LEVEL is INFO
  - **Purpose**: Ensure INFO is used without environment variable

- **`test_log_level_from_environment()`**:
  - **What it does**: Verifies LOG_LEVEL loading from environment variable
  - **Purpose**: Ensure value from environment is used

- **`test_log_level_uppercase_conversion()`**:
  - **What it does**: Verifies LOG_LEVEL conversion to uppercase
  - **Purpose**: Ensure lowercase value is converted to uppercase

- **`test_log_level_trace()`**:
  - **What it does**: Verifies LOG_LEVEL=TRACE setting
  - **Purpose**: Ensure TRACE level is supported

- **`test_log_level_error()`**:
  - **What it does**: Verifies LOG_LEVEL=ERROR setting
  - **Purpose**: Ensure ERROR level is supported

- **`test_log_level_critical()`**:
  - **What it does**: Verifies LOG_LEVEL=CRITICAL setting
  - **Purpose**: Ensure CRITICAL level is supported

#### `TestToolDescriptionMaxLengthConfig`

Tests for TOOL_DESCRIPTION_MAX_LENGTH configuration.

- **`test_default_tool_description_max_length()`**:
  - **What it does**: Verifies default value for TOOL_DESCRIPTION_MAX_LENGTH
  - **Purpose**: Ensure default is 10000

- **`test_tool_description_max_length_from_environment()`**:
  - **What it does**: Verifies TOOL_DESCRIPTION_MAX_LENGTH loading from environment
  - **Purpose**: Ensure value from environment is used

- **`test_tool_description_max_length_zero_disables()`**:
  - **What it does**: Verifies that 0 disables the feature
  - **Purpose**: Ensure TOOL_DESCRIPTION_MAX_LENGTH=0 works

#### `TestTimeoutConfigurationWarning`

Tests for `_warn_timeout_configuration()` function.

- **`test_no_warning_when_first_token_less_than_streaming()`**:
  - **What it does**: Verifies no warning when FIRST_TOKEN_TIMEOUT < STREAMING_READ_TIMEOUT
  - **Purpose**: Ensure correct configuration doesn't trigger warning

- **`test_warning_when_first_token_equals_streaming()`**:
  - **What it does**: Verifies warning when FIRST_TOKEN_TIMEOUT == STREAMING_READ_TIMEOUT
  - **Purpose**: Ensure equal timeouts trigger warning

- **`test_warning_when_first_token_greater_than_streaming()`**:
  - **What it does**: Verifies warning when FIRST_TOKEN_TIMEOUT > STREAMING_READ_TIMEOUT
  - **Purpose**: Ensure suboptimal configuration triggers warning with timeout values

- **`test_warning_contains_recommendation()`**:
  - **What it does**: Verifies warning contains recommendation text
  - **Purpose**: Ensure user gets helpful information about correct configuration

#### `TestAwsSsoOidcUrlConfig`

Tests for AWS SSO OIDC URL configuration.

- **`test_aws_sso_oidc_url_template_exists()`**:
  - **What it does**: Verifies AWS_SSO_OIDC_URL_TEMPLATE constant exists
  - **Purpose**: Ensure the template is defined in config

- **`test_get_aws_sso_oidc_url_returns_correct_url()`**:
  - **What it does**: Verifies get_aws_sso_oidc_url returns correct URL
  - **Purpose**: Ensure the function formats URL correctly

- **`test_get_aws_sso_oidc_url_with_different_regions()`**:
  - **What it does**: Verifies URL generation for different regions
  - **Purpose**: Ensure the function works with various AWS regions

#### `TestKiroCliDbFileConfig`

Tests for KIRO_CLI_DB_FILE configuration.

- **`test_kiro_cli_db_file_config_exists()`**:
  - **What it does**: Verifies KIRO_CLI_DB_FILE constant exists
  - **Purpose**: Ensure the config parameter is defined

- **`test_kiro_cli_db_file_from_environment()`**:
  - **What it does**: Verifies loading KIRO_CLI_DB_FILE from environment variable
  - **Purpose**: Ensure the value from environment is used

---

### `tests/unit/test_debug_logger.py`

Unit tests for **DebugLogger** (debug request logging). **26 tests.**

#### `TestDebugLoggerModeOff`

Tests for DEBUG_MODE=off mode.

- **`test_prepare_new_request_does_nothing()`**:
  - **What it does**: Verifies that prepare_new_request does nothing in off mode
  - **Purpose**: Ensure directory is not created in off mode

- **`test_log_request_body_does_nothing()`**:
  - **What it does**: Verifies that log_request_body does nothing in off mode
  - **Purpose**: Ensure data is not written

#### `TestDebugLoggerModeAll`

Tests for DEBUG_MODE=all mode.

- **`test_prepare_new_request_clears_directory()`**:
  - **What it does**: Verifies that prepare_new_request clears directory in all mode
  - **Purpose**: Ensure old logs are deleted

- **`test_log_request_body_writes_immediately()`**:
  - **What it does**: Verifies that log_request_body writes immediately to file in all mode
  - **Purpose**: Ensure data is written immediately

- **`test_log_kiro_request_body_writes_immediately()`**:
  - **What it does**: Verifies that log_kiro_request_body writes immediately to file in all mode
  - **Purpose**: Ensure Kiro payload is written immediately

- **`test_log_raw_chunk_appends_to_file()`**:
  - **What it does**: Verifies that log_raw_chunk appends to file in all mode
  - **Purpose**: Ensure chunks accumulate

#### `TestDebugLoggerModeErrors`

Tests for DEBUG_MODE=errors mode.

- **`test_log_request_body_buffers_data()`**:
  - **What it does**: Verifies that log_request_body buffers data in errors mode
  - **Purpose**: Ensure data is not written immediately

- **`test_flush_on_error_writes_buffers()`**:
  - **What it does**: Verifies that flush_on_error writes buffers to files
  - **Purpose**: Ensure data is saved on error

- **`test_flush_on_error_clears_buffers()`**:
  - **What it does**: Verifies that flush_on_error clears buffers after writing
  - **Purpose**: Ensure buffers don't accumulate between requests

- **`test_discard_buffers_clears_without_writing()`**:
  - **What it does**: Verifies that discard_buffers clears buffers without writing
  - **Purpose**: Ensure successful requests don't leave logs

- **`test_flush_on_error_writes_error_info_in_mode_all()`**:
  - **What it does**: Verifies that flush_on_error writes error_info.json in all mode
  - **Purpose**: Ensure error information is saved in both modes

#### `TestDebugLoggerLogErrorInfo`

Tests for log_error_info() method.

- **`test_log_error_info_writes_in_mode_all()`**:
  - **What it does**: Verifies that log_error_info writes file in all mode
  - **Purpose**: Ensure error_info.json is created on errors

- **`test_log_error_info_writes_in_mode_errors()`**:
  - **What it does**: Verifies that log_error_info writes file in errors mode
  - **Purpose**: Ensure method works in both modes

- **`test_log_error_info_does_nothing_in_mode_off()`**:
  - **What it does**: Verifies that log_error_info does nothing in off mode
  - **Purpose**: Ensure files are not created in off mode

#### `TestDebugLoggerHelperMethods`

Tests for DebugLogger helper methods.

- **`test_is_enabled_returns_true_for_errors()`**: Verifies _is_enabled() for errors mode
- **`test_is_enabled_returns_true_for_all()`**: Verifies _is_enabled() for all mode
- **`test_is_enabled_returns_false_for_off()`**: Verifies _is_enabled() for off mode
- **`test_is_immediate_write_returns_true_for_all()`**: Verifies _is_immediate_write() for all mode
- **`test_is_immediate_write_returns_false_for_errors()`**: Verifies _is_immediate_write() for errors mode

#### `TestDebugLoggerJsonHandling`

Tests for JSON handling in DebugLogger.

- **`test_log_request_body_formats_json_pretty()`**:
  - **What it does**: Verifies that JSON is formatted prettily
  - **Purpose**: Ensure JSON is readable in file

- **`test_log_request_body_handles_invalid_json()`**:
  - **What it does**: Verifies handling of invalid JSON
  - **Purpose**: Ensure invalid JSON is written as-is

#### `TestDebugLoggerAppLogsCapture`

Tests for application log capture (app_logs.txt).

- **`test_prepare_new_request_sets_up_log_capture()`**:
  - **What it does**: Verifies that prepare_new_request sets up log capture
  - **Purpose**: Ensure sink for logs is created

- **`test_flush_on_error_writes_app_logs_in_mode_errors()`**:
  - **What it does**: Verifies that flush_on_error writes app_logs.txt in errors mode
  - **Purpose**: Ensure application logs are saved on errors

- **`test_discard_buffers_saves_logs_in_mode_all()`**:
  - **What it does**: Verifies that discard_buffers saves logs in all mode
  - **Purpose**: Ensure even successful requests save logs in all mode

- **`test_discard_buffers_does_not_save_logs_in_mode_errors()`**:
  - **What it does**: Verifies that discard_buffers does NOT save logs in errors mode
  - **Purpose**: Ensure successful requests don't leave logs in errors mode

- **`test_clear_app_logs_buffer_removes_sink()`**:
  - **What it does**: Verifies that _clear_app_logs_buffer removes sink
  - **Purpose**: Ensure sink is correctly removed

- **`test_app_logs_not_saved_when_empty()`**:
  - **What it does**: Verifies that empty logs don't create file
  - **Purpose**: Ensure app_logs.txt is not created if there are no logs

---

### `tests/unit/test_converters_anthropic.py`

Unit tests for **Anthropic Messages API → Kiro** converters. **45 tests.**

#### `TestConvertAnthropicContentToText`

- **`test_extracts_from_string()`**:
  - **What it does**: Verifies text extraction from a string
  - **Purpose**: Ensure string is returned as-is

- **`test_extracts_from_list_with_text_blocks()`**:
  - **What it does**: Verifies extraction from list of text content blocks
  - **Purpose**: Ensure Anthropic multimodal format is handled

- **`test_extracts_from_pydantic_text_blocks()`**:
  - **What it does**: Verifies extraction from Pydantic TextContentBlock objects
  - **Purpose**: Ensure Pydantic models are handled correctly

- **`test_ignores_non_text_blocks()`**:
  - **What it does**: Verifies that non-text blocks are ignored
  - **Purpose**: Ensure tool_use and tool_result blocks don't contribute to text

- **`test_handles_none()`**:
  - **What it does**: Verifies None handling
  - **Purpose**: Ensure None returns empty string

- **`test_handles_empty_list()`**:
  - **What it does**: Verifies empty list handling
  - **Purpose**: Ensure empty list returns empty string

- **`test_converts_other_types_to_string()`**:
  - **What it does**: Verifies conversion of other types to string
  - **Purpose**: Ensure numbers and other types are converted

#### `TestExtractSystemPrompt`

Tests for extract_system_prompt function (Support System commit - prompt caching support).

- **`test_extracts_from_string()`**:
  - **What it does**: Verifies extraction from simple string
  - **Purpose**: Ensure string system prompt is returned as-is

- **`test_extracts_from_list_with_text_blocks()`**:
  - **What it does**: Verifies extraction from list of content blocks
  - **Purpose**: Ensure Anthropic prompt caching format is handled

- **`test_extracts_from_list_with_cache_control()`**:
  - **What it does**: Verifies extraction ignores cache_control field
  - **Purpose**: Ensure cache_control is stripped (not supported by Kiro)

- **`test_extracts_from_pydantic_system_content_blocks()`**:
  - **What it does**: Verifies extraction from Pydantic SystemContentBlock objects
  - **Purpose**: Ensure Pydantic models are handled correctly

- **`test_handles_none()`**:
  - **What it does**: Verifies None handling
  - **Purpose**: Ensure None returns empty string

- **`test_handles_empty_list()`**:
  - **What it does**: Verifies empty list handling
  - **Purpose**: Ensure empty list returns empty string

- **`test_handles_mixed_content_blocks()`**:
  - **What it does**: Verifies handling of list with non-text blocks
  - **Purpose**: Ensure only text blocks are extracted

- **`test_converts_other_types_to_string()`**:
  - **What it does**: Verifies conversion of other types to string
  - **Purpose**: Ensure numbers and other types are converted

- **`test_handles_single_text_block()`**:
  - **What it does**: Verifies extraction from single text block in list
  - **Purpose**: Ensure single block list works correctly

- **`test_handles_empty_text_in_block()`**:
  - **What it does**: Verifies handling of empty text in content block
  - **Purpose**: Ensure empty text doesn't cause errors

- **`test_handles_missing_text_key()`**:
  - **What it does**: Verifies handling of content block without text key
  - **Purpose**: Ensure missing text key doesn't cause errors

#### `TestExtractToolResultsFromAnthropicContent`

- **`test_extracts_tool_result_from_dict()`**:
  - **What it does**: Verifies extraction of tool result from dict content block
  - **Purpose**: Ensure tool_result blocks are extracted correctly

- **`test_extracts_tool_result_from_pydantic_model()`**:
  - **What it does**: Verifies extraction from Pydantic ToolResultContentBlock
  - **Purpose**: Ensure Pydantic models are handled correctly

- **`test_extracts_multiple_tool_results()`**:
  - **What it does**: Verifies extraction of multiple tool results
  - **Purpose**: Ensure all tool_result blocks are extracted

- **`test_returns_empty_for_string_content()`**:
  - **What it does**: Verifies empty list return for string content
  - **Purpose**: Ensure string doesn't contain tool results

- **`test_returns_empty_for_list_without_tool_results()`**:
  - **What it does**: Verifies empty list return without tool_result blocks
  - **Purpose**: Ensure regular elements are not extracted

- **`test_handles_empty_content_in_tool_result()`**:
  - **What it does**: Verifies handling of empty content in tool_result
  - **Purpose**: Ensure empty content is replaced with "(empty result)"

- **`test_handles_none_content_in_tool_result()`**:
  - **What it does**: Verifies handling of None content in tool_result
  - **Purpose**: Ensure None content is replaced with "(empty result)"

- **`test_handles_list_content_in_tool_result()`**:
  - **What it does**: Verifies handling of list content in tool_result
  - **Purpose**: Ensure list content is converted to text

- **`test_skips_tool_result_without_tool_use_id()`**:
  - **What it does**: Verifies that tool_result without tool_use_id is skipped
  - **Purpose**: Ensure invalid tool_result blocks are ignored

#### `TestExtractToolUsesFromAnthropicContent`

- **`test_extracts_tool_use_from_dict()`**:
  - **What it does**: Verifies extraction of tool use from dict content block
  - **Purpose**: Ensure tool_use blocks are extracted correctly

- **`test_extracts_tool_use_from_pydantic_model()`**:
  - **What it does**: Verifies extraction from Pydantic ToolUseContentBlock
  - **Purpose**: Ensure Pydantic models are handled correctly

- **`test_extracts_multiple_tool_uses()`**:
  - **What it does**: Verifies extraction of multiple tool uses
  - **Purpose**: Ensure all tool_use blocks are extracted

- **`test_returns_empty_for_string_content()`**:
  - **What it does**: Verifies empty list return for string content
  - **Purpose**: Ensure string doesn't contain tool uses

- **`test_returns_empty_for_list_without_tool_uses()`**:
  - **What it does**: Verifies empty list return without tool_use blocks
  - **Purpose**: Ensure regular elements are not extracted

- **`test_skips_tool_use_without_id()`**:
  - **What it does**: Verifies that tool_use without id is skipped
  - **Purpose**: Ensure invalid tool_use blocks are ignored

- **`test_skips_tool_use_without_name()`**:
  - **What it does**: Verifies that tool_use without name is skipped
  - **Purpose**: Ensure invalid tool_use blocks are ignored

#### `TestConvertAnthropicMessages`

- **`test_converts_simple_user_message()`**:
  - **What it does**: Verifies conversion of simple user message
  - **Purpose**: Ensure basic user message is converted to UnifiedMessage

- **`test_converts_simple_assistant_message()`**:
  - **What it does**: Verifies conversion of simple assistant message
  - **Purpose**: Ensure basic assistant message is converted to UnifiedMessage

- **`test_converts_user_message_with_content_blocks()`**:
  - **What it does**: Verifies conversion of user message with content blocks
  - **Purpose**: Ensure multimodal content is handled

- **`test_converts_assistant_message_with_tool_use()`**:
  - **What it does**: Verifies conversion of assistant message with tool_use
  - **Purpose**: Ensure tool_use blocks are extracted as tool_calls

- **`test_converts_user_message_with_tool_result()`**:
  - **What it does**: Verifies conversion of user message with tool_result
  - **Purpose**: Ensure tool_result blocks are extracted as tool_results

- **`test_converts_full_conversation()`**:
  - **What it does**: Verifies conversion of full conversation
  - **Purpose**: Ensure multi-turn conversation is converted correctly

- **`test_handles_empty_messages_list()`**:
  - **What it does**: Verifies handling of empty messages list
  - **Purpose**: Ensure empty list returns empty list

#### `TestConvertAnthropicTools`

- **`test_returns_none_for_none()`**:
  - **What it does**: Verifies handling of None
  - **Purpose**: Ensure None returns None

- **`test_returns_none_for_empty_list()`**:
  - **What it does**: Verifies handling of empty list
  - **Purpose**: Ensure empty list returns None

- **`test_converts_tool_from_pydantic_model()`**:
  - **What it does**: Verifies conversion of Pydantic AnthropicTool
  - **Purpose**: Ensure Pydantic models are converted to UnifiedTool

- **`test_converts_tool_from_dict()`**:
  - **What it does**: Verifies conversion of dict tool
  - **Purpose**: Ensure dict tools are converted to UnifiedTool

- **`test_converts_multiple_tools()`**:
  - **What it does**: Verifies conversion of multiple tools
  - **Purpose**: Ensure all tools are converted

- **`test_handles_tool_without_description()`**:
  - **What it does**: Verifies handling of tool without description
  - **Purpose**: Ensure None description is preserved

#### `TestAnthropicToKiro`

Main entry point tests for anthropic_to_kiro function.

- **`test_builds_simple_payload()`**:
  - **What it does**: Verifies building of simple Kiro payload
  - **Purpose**: Ensure basic request is converted correctly

- **`test_includes_system_prompt()`**:
  - **What it does**: Verifies that system prompt is included
  - **Purpose**: Ensure Anthropic's separate system field is handled

- **`test_includes_tools()`**:
  - **What it does**: Verifies that tools are included in payload
  - **Purpose**: Ensure Anthropic tools are converted to Kiro format

- **`test_builds_history_for_multi_turn()`**:
  - **What it does**: Verifies building of history for multi-turn conversation
  - **Purpose**: Ensure conversation history is included in payload

- **`test_handles_tool_use_and_result_flow()`**:
  - **What it does**: Verifies handling of tool use and result flow
  - **Purpose**: Ensure full tool flow is converted correctly

- **`test_raises_for_empty_messages()`**:
  - **What it does**: Verifies that empty messages raise Pydantic ValidationError
  - **Purpose**: Ensure Pydantic validation works correctly (min_length=1)

- **`test_injects_thinking_tags_when_enabled()`**:
  - **What it does**: Verifies that thinking tags are injected when enabled
  - **Purpose**: Ensure fake reasoning feature works with Anthropic API

- **`test_injects_thinking_tags_even_when_tool_results_present()`**:
  - **What it does**: Verifies that thinking tags ARE injected even when tool results are present
  - **Purpose**: Extended thinking should work in all scenarios including tool use flows

---

### `tests/unit/test_converters_core.py`

Unit tests for **shared conversion logic** used by both OpenAI and Anthropic adapters. **86 tests.**

#### `TestExtractTextContent`

- **`test_extracts_from_string()`**:
  - **What it does**: Verifies text extraction from a string
  - **Purpose**: Ensure string is returned as-is

- **`test_extracts_from_none()`**:
  - **What it does**: Verifies None handling
  - **Purpose**: Ensure None returns empty string

- **`test_extracts_from_list_with_text_type()`**:
  - **What it does**: Verifies extraction from list with type=text
  - **Purpose**: Ensure multimodal format is handled

- **`test_extracts_from_list_with_text_key()`**:
  - **What it does**: Verifies extraction from list with text key
  - **Purpose**: Ensure alternative format is handled

- **`test_extracts_from_list_with_strings()`**:
  - **What it does**: Verifies extraction from list of strings
  - **Purpose**: Ensure string list is concatenated

- **`test_extracts_from_mixed_list()`**:
  - **What it does**: Verifies extraction from mixed list
  - **Purpose**: Ensure different formats in one list are handled

- **`test_converts_other_types_to_string()`**:
  - **What it does**: Verifies conversion of other types to string
  - **Purpose**: Ensure numbers and other types are converted

- **`test_handles_empty_list()`**:
  - **What it does**: Verifies empty list handling
  - **Purpose**: Ensure empty list returns empty string

#### `TestMergeAdjacentMessages`

Tests for merge_adjacent_messages function using UnifiedMessage.

- **`test_merges_adjacent_user_messages()`**:
  - **What it does**: Verifies merging of adjacent user messages
  - **Purpose**: Ensure messages with the same role are merged

- **`test_preserves_alternating_messages()`**:
  - **What it does**: Verifies preservation of alternating messages
  - **Purpose**: Ensure different roles are not merged

- **`test_handles_empty_list()`**:
  - **What it does**: Verifies empty list handling
  - **Purpose**: Ensure empty list doesn't cause errors

- **`test_handles_single_message()`**:
  - **What it does**: Verifies single message handling
  - **Purpose**: Ensure single message is returned as-is

- **`test_merges_multiple_adjacent_groups()`**:
  - **What it does**: Verifies merging of multiple groups
  - **Purpose**: Ensure multiple groups of adjacent messages are merged

- **`test_merges_list_contents_correctly()`**:
  - **What it does**: Verifies merging of list contents
  - **Purpose**: Ensure lists are merged correctly

- **`test_merges_adjacent_assistant_tool_calls()`**:
  - **What it does**: Verifies tool_calls merging when merging adjacent assistant messages
  - **Purpose**: Ensure tool_calls from all assistant messages are preserved when merging

- **`test_merges_three_adjacent_assistant_tool_calls()`**:
  - **What it does**: Verifies tool_calls merging from three assistant messages
  - **Purpose**: Ensure all tool_calls are preserved when merging more than two messages

- **`test_merges_assistant_with_and_without_tool_calls()`**:
  - **What it does**: Verifies merging assistant with and without tool_calls
  - **Purpose**: Ensure tool_calls are correctly initialized when merging

- **`test_merges_user_messages_with_tool_results()`**:
  - **What it does**: Verifies merging of user messages with tool_results
  - **Purpose**: Ensure tool_results are preserved when merging user messages

#### `TestSanitizeJsonSchema`

Tests for sanitize_json_schema function that cleans JSON Schema from fields not supported by Kiro API.

- **`test_returns_empty_dict_for_none()`**:
  - **What it does**: Verifies None handling
  - **Purpose**: Ensure None returns empty dict

- **`test_returns_empty_dict_for_empty_dict()`**:
  - **What it does**: Verifies empty dict handling
  - **Purpose**: Ensure empty dict is returned as-is

- **`test_removes_empty_required_array()`**:
  - **What it does**: Verifies removal of empty required array
  - **Purpose**: Ensure `required: []` is removed from schema (critical for Cline bug)

- **`test_preserves_non_empty_required_array()`**:
  - **What it does**: Verifies preservation of non-empty required array
  - **Purpose**: Ensure required with elements is preserved

- **`test_removes_additional_properties()`**:
  - **What it does**: Verifies additionalProperties removal
  - **Purpose**: Ensure additionalProperties is removed from schema

- **`test_removes_both_empty_required_and_additional_properties()`**:
  - **What it does**: Verifies removal of both problematic fields
  - **Purpose**: Ensure both fields are removed simultaneously

- **`test_recursively_sanitizes_nested_properties()`**:
  - **What it does**: Verifies recursive sanitization of nested properties
  - **Purpose**: Ensure nested schemas are also sanitized

- **`test_sanitizes_items_in_lists()`**:
  - **What it does**: Verifies sanitization of items in lists (anyOf, oneOf)
  - **Purpose**: Ensure list elements are also sanitized

- **`test_preserves_non_dict_list_items()`**:
  - **What it does**: Verifies preservation of non-dict list items
  - **Purpose**: Ensure strings and other types in lists are preserved

- **`test_complex_real_world_schema()`**:
  - **What it does**: Verifies sanitization of real complex schema
  - **Purpose**: Ensure real schemas are handled correctly

#### `TestExtractToolResults`

- **`test_extracts_tool_results_from_list()`**:
  - **What it does**: Verifies extraction of tool results from list
  - **Purpose**: Ensure tool_result elements are extracted

- **`test_returns_empty_for_string_content()`**:
  - **What it does**: Verifies empty list return for string
  - **Purpose**: Ensure string doesn't contain tool results

- **`test_returns_empty_for_list_without_tool_results()`**:
  - **What it does**: Verifies empty list return without tool_result
  - **Purpose**: Ensure regular elements are not extracted

- **`test_extracts_multiple_tool_results()`**:
  - **What it does**: Verifies extraction of multiple tool results
  - **Purpose**: Ensure all tool_result elements are extracted

#### `TestConvertToolResultsToKiroFormat`

Tests for convert_tool_results_to_kiro_format function that converts unified tool results format (snake_case) to Kiro API format (camelCase). This is a critical function for fixing the 400 "Improperly formed request" bug.

- **`test_converts_single_tool_result()`**:
  - **What it does**: Verifies conversion of a single tool result
  - **Purpose**: Ensure basic conversion from unified to Kiro format works

- **`test_converts_multiple_tool_results()`**:
  - **What it does**: Verifies conversion of multiple tool results
  - **Purpose**: Ensure all tool results are converted correctly

- **`test_returns_empty_list_for_empty_input()`**:
  - **What it does**: Verifies empty list handling
  - **Purpose**: Ensure empty input returns empty output

- **`test_replaces_empty_content_with_placeholder()`**:
  - **What it does**: Verifies empty content is replaced with placeholder
  - **Purpose**: Ensure Kiro API receives non-empty content (required by API)

- **`test_replaces_none_content_with_placeholder()`**:
  - **What it does**: Verifies None content is replaced with placeholder
  - **Purpose**: Ensure Kiro API receives non-empty content when content is None

- **`test_handles_missing_content_key()`**:
  - **What it does**: Verifies handling of missing content key
  - **Purpose**: Ensure function doesn't crash when content key is missing

- **`test_handles_missing_tool_use_id()`**:
  - **What it does**: Verifies handling of missing tool_use_id
  - **Purpose**: Ensure function returns empty string for missing tool_use_id

- **`test_extracts_text_from_list_content()`**:
  - **What it does**: Verifies extraction of text from list content
  - **Purpose**: Ensure multimodal content format is handled correctly

- **`test_preserves_long_content()`**:
  - **What it does**: Verifies long content is preserved
  - **Purpose**: Ensure large tool results are not truncated

- **`test_all_results_have_success_status()`**:
  - **What it does**: Verifies all results have status="success"
  - **Purpose**: Ensure Kiro API receives correct status field

- **`test_handles_unicode_content()`**:
  - **What it does**: Verifies Unicode content is preserved
  - **Purpose**: Ensure non-ASCII characters are handled correctly

#### `TestExtractToolUses`

- **`test_extracts_from_tool_calls_field()`**:
  - **What it does**: Verifies extraction from tool_calls field
  - **Purpose**: Ensure OpenAI tool_calls format is handled

- **`test_extracts_from_content_list()`**:
  - **What it does**: Verifies extraction from content list
  - **Purpose**: Ensure tool_use in content is handled (Anthropic format)

- **`test_returns_empty_for_no_tool_uses()`**:
  - **What it does**: Verifies empty list return without tool uses
  - **Purpose**: Ensure regular message doesn't contain tool uses

- **`test_extracts_from_both_sources()`**:
  - **What it does**: Verifies extraction from both tool_calls and content
  - **Purpose**: Ensure both sources are combined

#### `TestProcessToolsWithLongDescriptions`

Tests for process_tools_with_long_descriptions function using UnifiedTool.

- **`test_returns_none_and_empty_string_for_none_tools()`**:
  - **What it does**: Verifies handling of None instead of tools list
  - **Purpose**: Ensure None returns (None, "")

- **`test_returns_none_and_empty_string_for_empty_list()`**:
  - **What it does**: Verifies handling of empty tools list
  - **Purpose**: Ensure empty list returns (None, "")

- **`test_short_description_unchanged()`**:
  - **What it does**: Verifies short descriptions are unchanged
  - **Purpose**: Ensure tools with short descriptions remain as-is

- **`test_long_description_moved_to_system_prompt()`**:
  - **What it does**: Verifies moving long description to system prompt
  - **Purpose**: Ensure long descriptions are moved correctly

- **`test_mixed_short_and_long_descriptions()`**:
  - **What it does**: Verifies handling of mixed tools list
  - **Purpose**: Ensure short ones stay, long ones are moved

- **`test_disabled_when_limit_is_zero()`**:
  - **What it does**: Verifies function is disabled when limit is 0
  - **Purpose**: Ensure tools are unchanged when TOOL_DESCRIPTION_MAX_LENGTH=0

- **`test_multiple_long_descriptions_all_moved()`**:
  - **What it does**: Verifies moving of multiple long descriptions
  - **Purpose**: Ensure all long descriptions are moved

- **`test_empty_description_unchanged()`**:
  - **What it does**: Verifies handling of empty description
  - **Purpose**: Ensure empty description doesn't cause errors

- **`test_none_description_unchanged()`**:
  - **What it does**: Verifies handling of None description
  - **Purpose**: Ensure None description doesn't cause errors

- **`test_preserves_tool_input_schema()`**:
  - **What it does**: Verifies input_schema preservation when moving description
  - **Purpose**: Ensure input_schema is not lost

#### `TestConvertToolsToKiroFormat`

- **`test_returns_empty_list_for_none()`**:
  - **What it does**: Verifies handling of None
  - **Purpose**: Ensure None returns empty list

- **`test_returns_empty_list_for_empty_list()`**:
  - **What it does**: Verifies handling of empty list
  - **Purpose**: Ensure empty list returns empty list

- **`test_converts_tool_to_kiro_format()`**:
  - **What it does**: Verifies conversion of tool to Kiro format
  - **Purpose**: Ensure toolSpecification structure is correct

- **`test_replaces_empty_description_with_placeholder()`**:
  - **What it does**: Verifies replacement of empty description
  - **Purpose**: Ensure empty description is replaced with "Tool: {name}"

- **`test_replaces_none_description_with_placeholder()`**:
  - **What it does**: Verifies replacement of None description
  - **Purpose**: Ensure None description is replaced with "Tool: {name}"

- **`test_sanitizes_input_schema()`**:
  - **What it does**: Verifies sanitization of input schema
  - **Purpose**: Ensure problematic fields are removed from schema

#### `TestInjectThinkingTags`

Tests for inject_thinking_tags function.

- **`test_returns_original_content_when_disabled()`**:
  - **What it does**: Verifies that content is returned unchanged when fake reasoning is disabled
  - **Purpose**: Ensure no modification occurs when FAKE_REASONING_ENABLED=False

- **`test_injects_tags_when_enabled()`**:
  - **What it does**: Verifies that thinking tags are injected when enabled
  - **Purpose**: Ensure tags are prepended to content when FAKE_REASONING_ENABLED=True

- **`test_injects_thinking_instruction_tag()`**:
  - **What it does**: Verifies that thinking_instruction tag is injected
  - **Purpose**: Ensure the quality improvement prompt is included

- **`test_thinking_instruction_contains_english_directive()`**:
  - **What it does**: Verifies that thinking instruction includes English language directive
  - **Purpose**: Ensure model is instructed to think in English for better reasoning quality

- **`test_uses_configured_max_tokens()`**:
  - **What it does**: Verifies that FAKE_REASONING_MAX_TOKENS config value is used
  - **Purpose**: Ensure the configured max tokens value is injected into the tag

- **`test_preserves_empty_content()`**:
  - **What it does**: Verifies that empty content is handled correctly
  - **Purpose**: Ensure empty string doesn't cause issues

- **`test_preserves_multiline_content()`**:
  - **What it does**: Verifies that multiline content is preserved correctly
  - **Purpose**: Ensure newlines in original content are not corrupted

- **`test_preserves_special_characters()`**:
  - **What it does**: Verifies that special characters in content are preserved
  - **Purpose**: Ensure XML-like content in user message doesn't break injection

- **`test_thinking_instruction_contains_systematic_approach()`**:
  - **What it does**: Verifies that thinking instruction includes systematic approach guidance
  - **Purpose**: Ensure model is instructed to think systematically

- **`test_thinking_instruction_contains_understanding_step()`**:
  - **What it does**: Verifies that thinking instruction includes understanding step
  - **Purpose**: Ensure model is instructed to understand the problem first

- **`test_thinking_instruction_contains_verification_step()`**:
  - **What it does**: Verifies that thinking instruction includes verification step
  - **Purpose**: Ensure model is instructed to verify reasoning before concluding

- **`test_thinking_instruction_contains_quality_emphasis()`**:
  - **What it does**: Verifies that thinking instruction emphasizes quality over speed
  - **Purpose**: Ensure model is instructed to prioritize quality of thought

- **`test_tag_order_is_correct()`**:
  - **What it does**: Verifies that tags are in the correct order
  - **Purpose**: Ensure thinking_mode comes first, then max_thinking_length, then instruction, then content

#### `TestBuildKiroHistory`

Tests for build_kiro_history function using UnifiedMessage.

- **`test_builds_user_message()`**:
  - **What it does**: Verifies building of user message
  - **Purpose**: Ensure user message is converted to userInputMessage

- **`test_builds_assistant_message()`**:
  - **What it does**: Verifies building of assistant message
  - **Purpose**: Ensure assistant message is converted to assistantResponseMessage

- **`test_ignores_system_messages()`**:
  - **What it does**: Verifies ignoring of system messages
  - **Purpose**: Ensure system messages are not added to history

- **`test_builds_conversation_history()`**:
  - **What it does**: Verifies building of full conversation history
  - **Purpose**: Ensure user/assistant alternation is preserved

- **`test_handles_empty_list()`**:
  - **What it does**: Verifies empty list handling
  - **Purpose**: Ensure empty list returns empty history

- **`test_builds_user_message_with_tool_results()`**:
  - **What it does**: Verifies building of user message with tool_results
  - **Purpose**: Ensure tool_results are included in userInputMessageContext

- **`test_builds_assistant_message_with_tool_calls()`**:
  - **What it does**: Verifies building of assistant message with tool_calls
  - **Purpose**: Ensure tool_calls are converted to toolUses

#### `TestStripAllToolContent`

Tests for strip_all_tool_content function that removes ALL tool-related content (tool_calls and tool_results) from messages. This is used when no tools are defined in the request, because Kiro API rejects requests that have toolResults but no tools defined.

- **`test_returns_empty_list_for_empty_input()`**:
  - **What it does**: Verifies empty list handling
  - **Purpose**: Ensure empty input returns empty output

- **`test_preserves_messages_without_tool_content()`**:
  - **What it does**: Verifies messages without tool content are unchanged
  - **Purpose**: Ensure regular messages pass through unmodified

- **`test_strips_tool_calls_from_assistant()`**:
  - **What it does**: Verifies tool_calls are stripped from assistant messages
  - **Purpose**: Ensure tool_calls are removed when no tools are defined

- **`test_strips_tool_results_from_user()`**:
  - **What it does**: Verifies tool_results are stripped from user messages
  - **Purpose**: Ensure tool_results are removed when no tools are defined

- **`test_strips_both_tool_calls_and_tool_results()`**:
  - **What it does**: Verifies both tool_calls and tool_results are stripped
  - **Purpose**: Ensure all tool content is removed in a conversation

- **`test_strips_multiple_tool_calls()`**:
  - **What it does**: Verifies multiple tool_calls are all stripped
  - **Purpose**: Ensure all tool_calls in a message are removed

- **`test_strips_multiple_tool_results()`**:
  - **What it does**: Verifies multiple tool_results are all stripped
  - **Purpose**: Ensure all tool_results in a message are removed

- **`test_preserves_message_content_when_stripping()`**:
  - **What it does**: Verifies message content is preserved when tool content is stripped
  - **Purpose**: Ensure only tool content is removed, not the entire message

- **`test_preserves_message_role_when_stripping()`**:
  - **What it does**: Verifies message role is preserved when tool content is stripped
  - **Purpose**: Ensure role is not modified during stripping

- **`test_mixed_messages_with_and_without_tool_content()`**:
  - **What it does**: Verifies correct handling of mixed messages
  - **Purpose**: Ensure only messages with tool content are modified

- **`test_returns_false_when_no_tool_content_stripped()`**:
  - **What it does**: Verifies had_content flag is False when no tool content exists
  - **Purpose**: Ensure correct flag value for messages without tool content

- **`test_returns_true_when_tool_content_stripped()`**:
  - **What it does**: Verifies had_content flag is True when tool content is stripped
  - **Purpose**: Ensure correct flag value for messages with tool content

- **`test_handles_empty_tool_calls_list()`**:
  - **What it does**: Verifies handling of empty tool_calls list
  - **Purpose**: Ensure empty list is treated as no tool content

- **`test_handles_empty_tool_results_list()`**:
  - **What it does**: Verifies handling of empty tool_results list
  - **Purpose**: Ensure empty list is treated as no tool content

---

### `tests/unit/test_converters_openai.py`

Unit tests for **OpenAI Chat API → Kiro** converters. **47 tests.**

#### `TestConvertOpenAIMessagesToUnified`

- **`test_extracts_system_prompt()`**:
  - **What it does**: Verifies extraction of system prompt from messages
  - **Purpose**: Ensure system messages are extracted separately

- **`test_combines_multiple_system_messages()`**:
  - **What it does**: Verifies combining of multiple system messages
  - **Purpose**: Ensure all system messages are concatenated

- **`test_converts_tool_message_to_user_with_tool_results()`**:
  - **What it does**: Verifies conversion of tool message to user message with tool_results
  - **Purpose**: Ensure role="tool" is converted correctly

- **`test_converts_multiple_tool_messages()`**:
  - **What it does**: Verifies conversion of multiple consecutive tool messages
  - **Purpose**: Ensure all tool results are collected into one user message

- **`test_extracts_tool_calls_from_assistant()`**:
  - **What it does**: Verifies extraction of tool_calls from assistant message
  - **Purpose**: Ensure tool_calls are preserved in unified format

- **`test_handles_empty_tool_call_id()`**:
  - **What it does**: Verifies handling of None tool_call_id
  - **Purpose**: Ensure None is replaced with empty string

- **`test_handles_empty_tool_content()`**:
  - **What it does**: Verifies handling of empty tool content
  - **Purpose**: Ensure empty content is replaced with "(empty result)"

- **`test_tool_messages_followed_by_user_message()`**:
  - **What it does**: Verifies tool messages followed by user message
  - **Purpose**: Ensure tool results are in separate message from user content

#### `TestConvertOpenAIToolsToUnified`

- **`test_returns_none_for_none()`**:
  - **What it does**: Verifies handling of None
  - **Purpose**: Ensure None returns None

- **`test_returns_none_for_empty_list()`**:
  - **What it does**: Verifies handling of empty list
  - **Purpose**: Ensure empty list returns None

- **`test_converts_function_tool()`**:
  - **What it does**: Verifies conversion of function tool
  - **Purpose**: Ensure Tool is converted to UnifiedTool

- **`test_skips_non_function_tools()`**:
  - **What it does**: Verifies skipping of non-function tools
  - **Purpose**: Ensure only function tools are converted

- **`test_converts_multiple_tools()`**:
  - **What it does**: Verifies conversion of multiple tools
  - **Purpose**: Ensure all function tools are converted

#### `TestBuildKiroPayload`

- **`test_builds_simple_payload()`**:
  - **What it does**: Verifies building of simple payload
  - **Purpose**: Ensure basic request is converted correctly

- **`test_includes_system_prompt_in_first_message()`**:
  - **What it does**: Verifies adding system prompt to first message
  - **Purpose**: Ensure system prompt is merged with user message

- **`test_builds_history_for_multi_turn()`**:
  - **What it does**: Verifies building history for multi-turn
  - **Purpose**: Ensure previous messages go into history

- **`test_handles_assistant_as_last_message()`**:
  - **What it does**: Verifies handling of assistant as last message
  - **Purpose**: Ensure "Continue" message is created

- **`test_raises_for_empty_messages()`**:
  - **What it does**: Verifies exception raising for empty messages
  - **Purpose**: Ensure empty request raises ValueError

- **`test_uses_continue_for_empty_content()`**:
  - **What it does**: Verifies using "Continue" for empty content
  - **Purpose**: Ensure empty message is replaced with "Continue"

- **`test_maps_model_id_correctly()`**:
  - **What it does**: Verifies mapping of external model ID to internal
  - **Purpose**: Ensure MODEL_MAPPING is applied

- **`test_includes_tools_in_context()`**:
  - **What it does**: Verifies including tools in userInputMessageContext
  - **Purpose**: Ensure tools are converted and included

- **`test_injects_thinking_tags_even_when_tool_results_present()`**:
  - **What it does**: Verifies thinking tags ARE injected even when toolResults are present
  - **Purpose**: Extended thinking should work in all scenarios including tool use flows

- **`test_injects_thinking_tags_when_no_tool_results()`**:
  - **What it does**: Verifies thinking tags ARE injected for normal user messages
  - **Purpose**: Ensure fix for issue #20 doesn't break normal thinking tag injection

#### `TestToolMessageHandling`

Tests for OpenAI tool message (role="tool") handling.

- **`test_converts_multiple_tool_messages_to_single_user_message()`**:
  - **What it does**: Verifies merging of multiple tool messages into single user message
  - **Purpose**: Ensure multiple tool results are merged into one user message

- **`test_assistant_tool_user_sequence()`**:
  - **What it does**: Verifies assistant -> tool -> user sequence
  - **Purpose**: Ensure tool message is correctly inserted between assistant and user

- **`test_tool_message_with_empty_content()`**:
  - **What it does**: Verifies tool message with empty content
  - **Purpose**: Ensure empty result is replaced with "(empty result)"

- **`test_tool_message_with_none_tool_call_id()`**:
  - **What it does**: Verifies tool message without tool_call_id
  - **Purpose**: Ensure missing tool_call_id is replaced with empty string

#### `TestToolDescriptionHandling`

Tests for handling empty/whitespace tool descriptions.

- **`test_empty_description_replaced_with_placeholder()`**:
  - **What it does**: Verifies replacement of empty description with placeholder
  - **Purpose**: Ensure empty description is replaced with "Tool: {name}" (critical for Cline bug with focus_chain)

- **`test_whitespace_only_description_replaced_with_placeholder()`**:
  - **What it does**: Verifies replacement of whitespace-only description with placeholder
  - **Purpose**: Ensure description with only whitespace is replaced

- **`test_none_description_replaced_with_placeholder()`**:
  - **What it does**: Verifies replacement of None description with placeholder
  - **Purpose**: Ensure None description is replaced with "Tool: {name}"

- **`test_non_empty_description_preserved()`**:
  - **What it does**: Verifies preservation of non-empty description
  - **Purpose**: Ensure normal description is not changed

- **`test_sanitizes_tool_parameters()`**:
  - **What it does**: Verifies sanitization of parameters from problematic fields
  - **Purpose**: Ensure sanitize_json_schema is applied to parameters

- **`test_mixed_tools_with_empty_and_normal_descriptions()`**:
  - **What it does**: Verifies handling of mixed tools list
  - **Purpose**: Ensure empty descriptions are replaced while normal ones are preserved (real scenario from Cline)

#### `TestBuildKiroPayloadToolCallsIntegration`

Integration tests for build_kiro_payload with tool_calls.

- **`test_multiple_assistant_tool_calls_with_results()`**:
  - **What it does**: Verifies full scenario with multiple assistant tool_calls and their results
  - **Purpose**: Ensure all toolUses and toolResults are correctly linked in Kiro payload

- **`test_long_tool_description_added_to_system_prompt()`**:
  - **What it does**: Verifies integration of long tool descriptions into payload
  - **Purpose**: Ensure long descriptions are added to system prompt in payload

---

### `tests/unit/test_parsers.py`

Unit tests for **AwsEventStreamParser** and helper parsing functions. **52 tests.**

#### `TestFindMatchingBrace`

- **`test_simple_json_object()`**: Verifies closing brace search for simple JSON
- **`test_nested_json_object()`**: Verifies search for nested JSON
- **`test_json_with_braces_in_string()`**: Verifies ignoring braces inside strings
- **`test_json_with_escaped_quotes()`**: Verifies handling of escaped quotes
- **`test_incomplete_json()`**: Verifies handling of incomplete JSON
- **`test_invalid_start_position()`**: Verifies handling of invalid start position
- **`test_start_position_out_of_bounds()`**: Verifies handling of position beyond text

#### `TestParseBracketToolCalls`

- **`test_parses_single_tool_call()`**: Verifies parsing of single tool call
- **`test_parses_multiple_tool_calls()`**: Verifies parsing of multiple tool calls
- **`test_returns_empty_for_no_tool_calls()`**: Verifies empty list return without tool calls
- **`test_returns_empty_for_empty_string()`**: Verifies empty string handling
- **`test_returns_empty_for_none()`**: Verifies None handling
- **`test_handles_nested_json_in_args()`**: Verifies parsing of nested JSON in arguments
- **`test_generates_unique_ids()`**: Verifies unique ID generation for tool calls

#### `TestDeduplicateToolCalls`

- **`test_removes_duplicates()`**: Verifies duplicate removal
- **`test_preserves_first_occurrence()`**: Verifies first occurrence preservation
- **`test_handles_empty_list()`**: Verifies empty list handling

**New tests for improved deduplication by id:**

- **`test_deduplicates_by_id_keeps_one_with_arguments()`**:
  - **What it does**: Verifies deduplication by id keeping tool call with arguments
  - **Purpose**: Ensure when duplicates by id, the one with arguments is kept

- **`test_deduplicates_by_id_prefers_longer_arguments()`**:
  - **What it does**: Verifies that duplicates by id prefer longer arguments
  - **Purpose**: Ensure tool call with more complete arguments is kept

- **`test_deduplicates_empty_arguments_replaced_by_non_empty()`**:
  - **What it does**: Verifies empty arguments replacement with non-empty
  - **Purpose**: Ensure "{}" is replaced with real arguments

- **`test_handles_tool_calls_without_id()`**:
  - **What it does**: Verifies handling of tool calls without id
  - **Purpose**: Ensure tool calls without id are deduplicated by name+arguments

- **`test_mixed_with_and_without_id()`**:
  - **What it does**: Verifies mixed list with and without id
  - **Purpose**: Ensure both types are handled correctly

#### `TestAwsEventStreamParserInitialization`

- **`test_initialization_creates_empty_state()`**: Verifies initial parser state

#### `TestAwsEventStreamParserFeed`

- **`test_parses_content_event()`**: Verifies content event parsing
- **`test_parses_multiple_content_events()`**: Verifies multiple content events parsing
- **`test_deduplicates_repeated_content()`**: Verifies repeated content deduplication
- **`test_parses_usage_event()`**: Verifies usage event parsing
- **`test_parses_context_usage_event()`**: Verifies context_usage event parsing
- **`test_handles_incomplete_json()`**: Verifies incomplete JSON handling
- **`test_completes_json_across_chunks()`**: Verifies JSON assembly from multiple chunks
- **`test_decodes_escape_sequences()`**: Verifies escape sequence decoding
- **`test_handles_invalid_bytes()`**: Verifies invalid bytes handling

#### `TestAwsEventStreamParserToolCalls`

- **`test_parses_tool_start_event()`**: Verifies tool call start parsing
- **`test_parses_tool_input_event()`**: Verifies tool call input parsing
- **`test_parses_tool_stop_event()`**: Verifies tool call completion
- **`test_get_tool_calls_returns_all()`**: Verifies getting all tool calls
- **`test_get_tool_calls_finalizes_current()`**: Verifies incomplete tool call finalization

#### `TestAwsEventStreamParserReset`

- **`test_reset_clears_state()`**: Verifies parser state reset

#### `TestAwsEventStreamParserFinalizeToolCall`

**New tests for _finalize_tool_call method with different input types:**

- **`test_finalize_with_string_arguments()`**:
  - **What it does**: Verifies tool call finalization with string arguments
  - **Purpose**: Ensure JSON string is parsed and serialized back

- **`test_finalize_with_dict_arguments()`**:
  - **What it does**: Verifies tool call finalization with dict arguments
  - **Purpose**: Ensure dict is serialized to JSON string

- **`test_finalize_with_empty_string_arguments()`**:
  - **What it does**: Verifies tool call finalization with empty string arguments
  - **Purpose**: Ensure empty string is replaced with "{}"

- **`test_finalize_with_whitespace_only_arguments()`**:
  - **What it does**: Verifies tool call finalization with whitespace arguments
  - **Purpose**: Ensure whitespace string is replaced with "{}"

- **`test_finalize_with_invalid_json_arguments()`**:
  - **What it does**: Verifies tool call finalization with invalid JSON
  - **Purpose**: Ensure invalid JSON is replaced with "{}"

- **`test_finalize_with_none_current_tool_call()`**:
  - **What it does**: Verifies finalization when current_tool_call is None
  - **Purpose**: Ensure nothing happens with None

- **`test_finalize_clears_current_tool_call()`**:
  - **What it does**: Verifies that finalization clears current_tool_call
  - **Purpose**: Ensure current_tool_call = None after finalization

#### `TestAwsEventStreamParserEdgeCases`

- **`test_handles_followup_prompt()`**: Verifies followupPrompt ignoring
- **`test_handles_mixed_events()`**: Verifies mixed events parsing
- **`test_handles_garbage_between_events()`**: Verifies garbage handling between events
- **`test_handles_empty_chunk()`**: Verifies empty chunk handling

---

### `tests/unit/test_thinking_parser.py`

Unit tests for **ThinkingParser** (FSM-based parser for thinking blocks in streaming responses). **63 tests.**

#### `TestParserStateEnum`

- **`test_pre_content_value()`**: Verifies PRE_CONTENT enum value is 0
- **`test_in_thinking_value()`**: Verifies IN_THINKING enum value is 1
- **`test_streaming_value()`**: Verifies STREAMING enum value is 2

#### `TestThinkingParseResult`

- **`test_default_values()`**: Verifies default values of ThinkingParseResult dataclass
- **`test_custom_values()`**: Verifies custom values can be set in ThinkingParseResult

#### `TestThinkingParserInitialization`

- **`test_default_initialization()`**: Verifies parser starts in PRE_CONTENT state with empty buffers
- **`test_custom_handling_mode()`**: Verifies handling_mode can be overridden
- **`test_custom_open_tags()`**: Verifies open_tags can be overridden
- **`test_custom_initial_buffer_size()`**: Verifies initial_buffer_size can be overridden
- **`test_max_tag_length_calculated()`**: Verifies max_tag_length is calculated from open_tags

#### `TestThinkingParserFeedPreContent`

- **`test_empty_content_returns_empty_result()`**: Verifies empty content doesn't change state
- **`test_detects_thinking_tag()`**: Verifies `<thinking>` tag detection and state transition
- **`test_detects_think_tag()`**: Verifies `<think>` tag detection
- **`test_detects_reasoning_tag()`**: Verifies `<reasoning>` tag detection
- **`test_detects_thought_tag()`**: Verifies `<thought>` tag detection
- **`test_strips_leading_whitespace_for_tag_detection()`**: Verifies leading whitespace is stripped
- **`test_buffers_partial_tag()`**: Verifies partial tag is buffered
- **`test_completes_partial_tag()`**: Verifies partial tag is completed across chunks
- **`test_no_tag_transitions_to_streaming()`**: Verifies transition to STREAMING when no tag found
- **`test_buffer_exceeds_limit_transitions_to_streaming()`**: Verifies transition when buffer exceeds limit

#### `TestThinkingParserFeedInThinking`

- **`test_accumulates_thinking_content()`**: Verifies thinking content is accumulated
- **`test_detects_closing_tag()`**: Verifies closing tag detection and state transition
- **`test_regular_content_after_closing_tag()`**: Verifies content after closing tag is regular_content
- **`test_strips_whitespace_after_closing_tag()`**: Verifies whitespace is stripped after closing tag
- **`test_cautious_buffering()`**: Verifies cautious buffering keeps last max_tag_length chars
- **`test_split_closing_tag()`**: Verifies split closing tag is handled

#### `TestThinkingParserFeedStreaming`

- **`test_passes_content_through()`**: Verifies content is passed through in STREAMING state
- **`test_ignores_thinking_tags_in_streaming()`**: Verifies thinking tags are ignored in STREAMING state

#### `TestThinkingParserFinalize`

- **`test_flushes_thinking_buffer()`**: Verifies thinking buffer is flushed on finalize
- **`test_flushes_initial_buffer()`**: Verifies initial buffer is flushed on finalize
- **`test_clears_buffers_after_finalize()`**: Verifies buffers are cleared after finalize

#### `TestThinkingParserReset`

- **`test_resets_to_initial_state()`**: Verifies reset returns parser to initial state

#### `TestThinkingParserFoundThinkingBlock`

- **`test_false_initially()`**: Verifies found_thinking_block is False initially
- **`test_true_after_tag_detection()`**: Verifies found_thinking_block is True after tag detection
- **`test_false_when_no_tag()`**: Verifies found_thinking_block is False when no tag found

#### `TestThinkingParserProcessForOutput`

- **`test_as_reasoning_content_mode()`**: Verifies as_reasoning_content mode returns content as-is
- **`test_remove_mode()`**: Verifies remove mode returns None
- **`test_pass_mode_first_chunk()`**: Verifies pass mode adds opening tag to first chunk
- **`test_pass_mode_last_chunk()`**: Verifies pass mode adds closing tag to last chunk
- **`test_pass_mode_first_and_last_chunk()`**: Verifies pass mode adds both tags when first and last
- **`test_pass_mode_middle_chunk()`**: Verifies pass mode returns content as-is for middle chunk
- **`test_strip_tags_mode()`**: Verifies strip_tags mode returns content without tags
- **`test_none_content_returns_none()`**: Verifies None content returns None
- **`test_empty_content_returns_none()`**: Verifies empty content returns None

#### `TestThinkingParserFullFlow`

Integration tests for full parsing flow.

- **`test_complete_thinking_block()`**: Verifies complete thinking block parsing
- **`test_multi_chunk_thinking_block()`**: Verifies thinking block split across multiple chunks
- **`test_no_thinking_block()`**: Verifies handling of content without thinking block
- **`test_thinking_block_with_newlines()`**: Verifies thinking block with newlines after closing tag
- **`test_empty_thinking_block()`**: Verifies empty thinking block handling
- **`test_thinking_block_only_whitespace_after()`**: Verifies thinking block with only whitespace after

#### `TestThinkingParserEdgeCases`

- **`test_nested_tags_not_supported()`**: Verifies nested tags are not specially handled
- **`test_tag_in_middle_of_content()`**: Verifies tag in middle of content is not detected
- **`test_malformed_closing_tag()`**: Verifies malformed closing tag is not detected
- **`test_unicode_content()`**: Verifies Unicode content is handled correctly
- **`test_very_long_thinking_content()`**: Verifies very long thinking content is handled
- **`test_special_characters_in_content()`**: Verifies special characters are handled
- **`test_multiple_feeds_after_streaming()`**: Verifies multiple feeds in STREAMING state

#### `TestThinkingParserConfigIntegration`

- **`test_uses_config_handling_mode()`**: Verifies parser uses FAKE_REASONING_HANDLING from config
- **`test_uses_config_open_tags()`**: Verifies parser uses FAKE_REASONING_OPEN_TAGS from config
- **`test_default_initial_buffer_size_from_config()`**: Verifies parser uses default initial_buffer_size from config

#### `TestInjectThinkingTags`

Tests for inject_thinking_tags function in converters.

- **`test_injects_tags_when_enabled()`**: Verifies tags are injected when FAKE_REASONING_ENABLED is True
- **`test_no_injection_when_disabled()`**: Verifies tags are not injected when FAKE_REASONING_ENABLED is False
- **`test_injection_preserves_content()`**: Verifies original content is preserved after injection

---

### `tests/unit/test_tokenizer.py`

Unit tests for **tokenizer module** (token counting with tiktoken). **32 tests.**

#### `TestCountTokens`

Tests for count_tokens function.

- **`test_empty_string_returns_zero()`**:
  - **What it does**: Verifies that empty string returns 0 tokens
  - **Purpose**: Ensure correct edge case handling

- **`test_none_returns_zero()`**:
  - **What it does**: Verifies that None returns 0 tokens
  - **Purpose**: Ensure correct None handling

- **`test_simple_text_returns_positive()`**:
  - **What it does**: Verifies that simple text returns positive token count
  - **Purpose**: Ensure basic counting functionality

- **`test_longer_text_returns_more_tokens()`**:
  - **What it does**: Verifies that longer text returns more tokens
  - **Purpose**: Ensure correct counting proportionality

- **`test_claude_correction_applied_by_default()`**:
  - **What it does**: Verifies that Claude correction factor is applied by default
  - **Purpose**: Ensure apply_claude_correction=True by default

- **`test_without_claude_correction()`**:
  - **What it does**: Verifies counting without correction factor
  - **Purpose**: Ensure apply_claude_correction=False works

- **`test_unicode_text()`**:
  - **What it does**: Verifies token counting for Unicode text
  - **Purpose**: Ensure correct non-ASCII character handling

- **`test_multiline_text()`**:
  - **What it does**: Verifies token counting for multiline text
  - **Purpose**: Ensure correct newline handling

- **`test_json_text()`**:
  - **What it does**: Verifies token counting for JSON string
  - **Purpose**: Ensure correct JSON handling

#### `TestCountTokensFallback`

Tests for fallback logic when tiktoken is unavailable.

- **`test_fallback_when_tiktoken_unavailable()`**:
  - **What it does**: Verifies fallback counting when tiktoken is unavailable
  - **Purpose**: Ensure system works without tiktoken

- **`test_fallback_without_correction()`**:
  - **What it does**: Verifies fallback without correction factor
  - **Purpose**: Ensure fallback works with apply_claude_correction=False

#### `TestCountMessageTokens`

Tests for count_message_tokens function.

- **`test_empty_list_returns_zero()`**:
  - **What it does**: Verifies that empty list returns 0 tokens
  - **Purpose**: Ensure correct empty list handling

- **`test_none_returns_zero()`**:
  - **What it does**: Verifies that None returns 0 tokens
  - **Purpose**: Ensure correct None handling

- **`test_single_user_message()`**:
  - **What it does**: Verifies token counting for single user message
  - **Purpose**: Ensure basic functionality

- **`test_multiple_messages()`**:
  - **What it does**: Verifies token counting for multiple messages
  - **Purpose**: Ensure tokens are summed correctly

- **`test_message_with_tool_calls()`**:
  - **What it does**: Verifies token counting for message with tool_calls
  - **Purpose**: Ensure tool_calls are counted

- **`test_message_with_tool_call_id()`**:
  - **What it does**: Verifies token counting for tool response message
  - **Purpose**: Ensure tool_call_id is counted

- **`test_message_with_list_content()`**:
  - **What it does**: Verifies token counting for multimodal content
  - **Purpose**: Ensure list content is handled

- **`test_without_claude_correction()`**:
  - **What it does**: Verifies counting without correction factor
  - **Purpose**: Ensure apply_claude_correction=False works

- **`test_message_with_empty_content()`**:
  - **What it does**: Verifies counting for message with empty content
  - **Purpose**: Ensure empty content doesn't break counting

- **`test_message_with_none_content()`**:
  - **What it does**: Verifies counting for message with None content
  - **Purpose**: Ensure None content doesn't break counting

#### `TestCountToolsTokens`

Tests for count_tools_tokens function.

- **`test_none_returns_zero()`**:
  - **What it does**: Verifies that None returns 0 tokens
  - **Purpose**: Ensure correct None handling

- **`test_empty_list_returns_zero()`**:
  - **What it does**: Verifies that empty list returns 0 tokens
  - **Purpose**: Ensure correct empty list handling

- **`test_single_tool()`**:
  - **What it does**: Verifies token counting for single tool
  - **Purpose**: Ensure basic functionality

- **`test_multiple_tools()`**:
  - **What it does**: Verifies token counting for multiple tools
  - **Purpose**: Ensure tokens are summed

- **`test_tool_with_complex_parameters()`**:
  - **What it does**: Verifies counting for tool with complex parameters
  - **Purpose**: Ensure JSON schema parameters are counted

- **`test_tool_without_parameters()`**:
  - **What it does**: Verifies counting for tool without parameters
  - **Purpose**: Ensure missing parameters doesn't break counting

- **`test_tool_with_empty_description()`**:
  - **What it does**: Verifies counting for tool with empty description
  - **Purpose**: Ensure empty description doesn't break counting

- **`test_non_function_tool_type()`**:
  - **What it does**: Verifies handling of tool with type != "function"
  - **Purpose**: Ensure non-function tools are handled

- **`test_without_claude_correction()`**:
  - **What it does**: Verifies counting without correction factor
  - **Purpose**: Ensure apply_claude_correction=False works

#### `TestEstimateRequestTokens`

Tests for estimate_request_tokens function.

- **`test_messages_only()`**:
  - **What it does**: Verifies token estimation for messages only
  - **Purpose**: Ensure basic functionality

- **`test_messages_with_tools()`**:
  - **What it does**: Verifies token estimation for messages with tools
  - **Purpose**: Ensure tools are counted

- **`test_messages_with_system_prompt()`**:
  - **What it does**: Verifies token estimation with separate system prompt
  - **Purpose**: Ensure system_prompt is counted

- **`test_full_request()`**:
  - **What it does**: Verifies token estimation for full request
  - **Purpose**: Ensure all components are summed

- **`test_empty_messages()`**:
  - **What it does**: Verifies estimation for empty message list
  - **Purpose**: Ensure correct edge case handling

#### `TestClaudeCorrectionFactor`

Tests for Claude correction factor.

- **`test_correction_factor_value()`**:
  - **What it does**: Verifies correction factor value
  - **Purpose**: Ensure factor equals 1.15

- **`test_correction_increases_token_count()`**:
  - **What it does**: Verifies that correction increases token count
  - **Purpose**: Ensure factor is applied correctly

#### `TestGetEncoding`

Tests for _get_encoding function.

- **`test_returns_encoding_when_tiktoken_available()`**:
  - **What it does**: Verifies that _get_encoding returns encoding when tiktoken is available
  - **Purpose**: Ensure correct tiktoken initialization

- **`test_caches_encoding()`**:
  - **What it does**: Verifies that encoding is cached
  - **Purpose**: Ensure lazy initialization

- **`test_handles_import_error()`**:
  - **What it does**: Verifies ImportError handling when tiktoken is missing
  - **Purpose**: Ensure system works without tiktoken

#### `TestTokenizerIntegration`

Integration tests for tokenizer.

- **`test_realistic_chat_request()`**:
  - **What it does**: Verifies token counting for realistic chat request
  - **Purpose**: Ensure correct operation on real data

- **`test_large_context()`**:
  - **What it does**: Verifies token counting for large context
  - **Purpose**: Ensure performance on large data

- **`test_consistency_across_calls()`**:
  - **What it does**: Verifies counting consistency across repeated calls
  - **Purpose**: Ensure results are deterministic

---

### `tests/unit/test_streaming_anthropic.py`

Unit tests for **Anthropic streaming module** (Kiro → Anthropic SSE format conversion). **48 tests.**

#### `TestGenerateMessageId`

- **`test_generates_message_id_with_prefix()`**:
  - **What it does**: Verifies message ID has 'msg_' prefix
  - **Purpose**: Ensure Anthropic message ID format

- **`test_generates_unique_ids()`**:
  - **What it does**: Verifies 100 generated IDs are unique
  - **Purpose**: Ensure ID uniqueness

- **`test_message_id_has_correct_length()`**:
  - **What it does**: Verifies message ID length (msg_ + 24 chars)
  - **Purpose**: Ensure ID format matches Anthropic spec

#### `TestFormatSseEvent`

- **`test_formats_message_start_event()`**:
  - **What it does**: Formats message_start event
  - **Purpose**: Verify Anthropic SSE format

- **`test_formats_content_block_delta_event()`**:
  - **What it does**: Formats content_block_delta event
  - **Purpose**: Verify delta event format

- **`test_formats_message_stop_event()`**:
  - **What it does**: Formats message_stop event
  - **Purpose**: Verify stop event format

- **`test_handles_unicode_content()`**:
  - **What it does**: Handles Unicode content in events
  - **Purpose**: Verify non-ASCII characters are preserved

- **`test_json_data_is_valid()`**:
  - **What it does**: Verifies JSON data is valid and parseable
  - **Purpose**: Ensure data can be parsed back

#### `TestStreamKiroToAnthropic`

- **`test_yields_message_start_event()`**:
  - **What it does**: Yields message_start event at beginning
  - **Purpose**: Verify Anthropic streaming protocol

- **`test_yields_content_block_start_on_first_content()`**:
  - **What it does**: Yields content_block_start before first content
  - **Purpose**: Verify content block lifecycle

- **`test_yields_content_block_delta_for_content()`**:
  - **What it does**: Yields content_block_delta for content events
  - **Purpose**: Verify content streaming

- **`test_yields_tool_use_block_for_tool_calls()`**:
  - **What it does**: Yields tool_use block for tool calls
  - **Purpose**: Verify tool use streaming

- **`test_yields_message_delta_with_stop_reason()`**:
  - **What it does**: Yields message_delta with stop_reason
  - **Purpose**: Verify message completion

- **`test_yields_message_stop_at_end()`**:
  - **What it does**: Yields message_stop at end
  - **Purpose**: Verify stream termination

- **`test_stop_reason_is_tool_use_when_tools_present()`**:
  - **What it does**: Sets stop_reason to tool_use when tools present
  - **Purpose**: Verify correct stop reason for tool calls

- **`test_handles_bracket_tool_calls()`**:
  - **What it does**: Handles bracket-style tool calls in content
  - **Purpose**: Verify bracket tool call detection

- **`test_closes_response_on_completion()`**:
  - **What it does**: Closes response on completion
  - **Purpose**: Verify resource cleanup

- **`test_closes_response_on_error()`**:
  - **What it does**: Closes response on error
  - **Purpose**: Verify resource cleanup on error

#### `TestCollectAnthropicResponse`

- **`test_collects_text_content()`**:
  - **What it does**: Collects text content into response
  - **Purpose**: Verify content collection

- **`test_collects_tool_use_content()`**:
  - **What it does**: Collects tool use into response
  - **Purpose**: Verify tool use collection

- **`test_sets_stop_reason_end_turn()`**:
  - **What it does**: Sets stop_reason to end_turn for normal completion
  - **Purpose**: Verify stop reason

- **`test_sets_stop_reason_tool_use()`**:
  - **What it does**: Sets stop_reason to tool_use when tools present
  - **Purpose**: Verify stop reason for tool calls

- **`test_includes_usage_info()`**:
  - **What it does**: Includes usage information in response
  - **Purpose**: Verify usage is included

- **`test_generates_message_id()`**:
  - **What it does**: Generates message ID for response
  - **Purpose**: Verify message ID is present

- **`test_includes_model_name()`**:
  - **What it does**: Includes model name in response
  - **Purpose**: Verify model is included

- **`test_parses_tool_arguments_from_string()`**:
  - **What it does**: Parses tool arguments from JSON string
  - **Purpose**: Verify arguments are parsed to dict

- **`test_handles_invalid_json_arguments()`**:
  - **What it does**: Handles invalid JSON in tool arguments
  - **Purpose**: Verify graceful handling of invalid JSON

- **`test_handles_empty_content()`**:
  - **What it does**: Handles empty content in response
  - **Purpose**: Verify empty content is handled

#### `TestStreamingAnthropicErrorHandling`

- **`test_propagates_first_token_timeout_error()`**:
  - **What it does**: Propagates FirstTokenTimeoutError
  - **Purpose**: Verify timeout error is not caught internally

- **`test_propagates_generator_exit()`**:
  - **What it does**: Propagates GeneratorExit
  - **Purpose**: Verify client disconnect is handled

- **`test_yields_error_event_on_exception()`**:
  - **What it does**: Yields error event on exception
  - **Purpose**: Verify error event is sent to client

- **`test_closes_response_in_finally()`**:
  - **What it does**: Closes response in finally block
  - **Purpose**: Verify resource cleanup always happens

#### `TestStreamingAnthropicThinkingContent`

- **`test_includes_thinking_as_text_when_configured()`**:
  - **What it does**: Includes thinking content as text when configured
  - **Purpose**: Verify thinking content handling

- **`test_strips_thinking_when_configured()`**:
  - **What it does**: Strips thinking content when configured
  - **Purpose**: Verify thinking content is stripped

#### `TestStreamingAnthropicContextUsage`

- **`test_calculates_tokens_from_context_usage()`**:
  - **What it does**: Calculates tokens from context usage percentage
  - **Purpose**: Verify token calculation

- **`test_uses_request_messages_for_input_tokens()`**:
  - **What it does**: Uses request messages for input token count
  - **Purpose**: Verify input tokens are counted from request

#### `TestGenerateThinkingSignature`

Tests for generate_thinking_signature() function that generates placeholder signatures for thinking content blocks.

- **`test_generates_signature_with_prefix()`**:
  - **What it does**: Generates signature with 'sig_' prefix
  - **Purpose**: Verify signature format matches expected pattern

- **`test_generates_unique_signatures()`**:
  - **What it does**: Generates unique signatures
  - **Purpose**: Verify signatures are unique across multiple calls

- **`test_signature_has_correct_length()`**:
  - **What it does**: Verifies signature length
  - **Purpose**: Ensure signature format is consistent (sig_ + 32 hex chars)

- **`test_signature_contains_only_valid_characters()`**:
  - **What it does**: Verifies signature contains only valid hex characters
  - **Purpose**: Ensure signature is properly formatted

#### `TestStreamWithFirstTokenRetryAnthropic`

Tests for stream_with_first_token_retry_anthropic() function that wraps stream_kiro_to_anthropic with automatic retry on first token timeout.

- **`test_yields_chunks_on_success()`**:
  - **What it does**: Yields chunks on successful streaming
  - **Purpose**: Verify normal operation without retries

- **`test_retries_on_first_token_timeout()`**:
  - **What it does**: Retries on first token timeout
  - **Purpose**: Verify retry logic is triggered

- **`test_raises_anthropic_error_after_all_retries()`**:
  - **What it does**: Raises Anthropic-formatted error after all retries exhausted
  - **Purpose**: Verify error format matches Anthropic API

- **`test_raises_anthropic_error_on_http_error()`**:
  - **What it does**: Raises Anthropic-formatted error on HTTP error
  - **Purpose**: Verify HTTP errors are formatted correctly

- **`test_passes_request_messages_to_stream()`**:
  - **What it does**: Passes request_messages to underlying stream function
  - **Purpose**: Verify token counting parameters are forwarded

- **`test_uses_configured_max_retries()`**:
  - **What it does**: Uses configured max_retries value
  - **Purpose**: Verify max_retries parameter is respected

---

### `tests/unit/test_streaming_core.py`

Unit tests for **core streaming module** (KiroEvent, StreamResult, parse_kiro_stream). **57 tests.**

#### `TestKiroEvent`

- **`test_creates_content_event()`**:
  - **What it does**: Creates a content event with text
  - **Purpose**: Verify KiroEvent can represent content events

- **`test_creates_thinking_event()`**:
  - **What it does**: Creates a thinking event with reasoning content
  - **Purpose**: Verify KiroEvent can represent thinking events

- **`test_creates_tool_use_event()`**:
  - **What it does**: Creates a tool_use event with tool data
  - **Purpose**: Verify KiroEvent can represent tool use events

- **`test_creates_usage_event()`**:
  - **What it does**: Creates a usage event with metering data
  - **Purpose**: Verify KiroEvent can represent usage events

- **`test_creates_context_usage_event()`**:
  - **What it does**: Creates a context_usage event with percentage
  - **Purpose**: Verify KiroEvent can represent context usage events

- **`test_default_values()`**:
  - **What it does**: Verifies default values for optional fields
  - **Purpose**: Ensure all optional fields default to None/False

#### `TestStreamResult`

- **`test_creates_empty_result()`**:
  - **What it does**: Creates an empty StreamResult
  - **Purpose**: Verify default values are correct

- **`test_creates_result_with_content()`**:
  - **What it does**: Creates StreamResult with content
  - **Purpose**: Verify content is stored correctly

- **`test_creates_result_with_tool_calls()`**:
  - **What it does**: Creates StreamResult with tool calls
  - **Purpose**: Verify tool calls are stored correctly

- **`test_creates_result_with_usage()`**:
  - **What it does**: Creates StreamResult with usage data
  - **Purpose**: Verify usage is stored correctly

- **`test_creates_full_result()`**:
  - **What it does**: Creates StreamResult with all fields
  - **Purpose**: Verify all fields work together

#### `TestFirstTokenTimeoutError`

- **`test_creates_exception_with_message()`**:
  - **What it does**: Creates exception with custom message
  - **Purpose**: Verify exception message is stored correctly

- **`test_exception_is_catchable()`**:
  - **What it does**: Verifies exception can be caught
  - **Purpose**: Ensure exception inherits from Exception

- **`test_exception_inherits_from_exception()`**:
  - **What it does**: Verifies inheritance chain
  - **Purpose**: Ensure proper exception hierarchy

#### `TestParseKiroStream`

- **`test_parses_content_events()`**:
  - **What it does**: Parses content events from Kiro stream
  - **Purpose**: Verify content events are yielded correctly

- **`test_parses_usage_events()`**:
  - **What it does**: Parses usage events from Kiro stream
  - **Purpose**: Verify usage events are yielded correctly

- **`test_parses_context_usage_events()`**:
  - **What it does**: Parses context_usage events from Kiro stream
  - **Purpose**: Verify context usage percentage is yielded correctly

- **`test_yields_tool_calls_at_end()`**:
  - **What it does**: Yields tool calls collected during parsing
  - **Purpose**: Verify tool calls are yielded as events

- **`test_raises_timeout_on_first_token()`**:
  - **What it does**: Raises FirstTokenTimeoutError on timeout
  - **Purpose**: Verify timeout handling for first token

- **`test_handles_empty_response()`**:
  - **What it does**: Handles empty response gracefully
  - **Purpose**: Verify no events yielded for empty response

- **`test_handles_generator_exit()`**:
  - **What it does**: Handles GeneratorExit gracefully
  - **Purpose**: Verify client disconnect is handled

#### `TestProcessChunk`

- **`test_processes_content_event()`**:
  - **What it does**: Processes content event from chunk
  - **Purpose**: Verify content is converted to KiroEvent

- **`test_processes_usage_event()`**:
  - **What it does**: Processes usage event from chunk
  - **Purpose**: Verify usage is converted to KiroEvent

- **`test_processes_context_usage_event()`**:
  - **What it does**: Processes context_usage event from chunk
  - **Purpose**: Verify context usage is converted to KiroEvent

- **`test_processes_multiple_events()`**:
  - **What it does**: Processes multiple events from single chunk
  - **Purpose**: Verify all events are yielded

- **`test_processes_with_thinking_parser()`**:
  - **What it does**: Processes content through thinking parser
  - **Purpose**: Verify thinking parser integration

- **`test_yields_thinking_content()`**:
  - **What it does**: Yields thinking content from thinking parser
  - **Purpose**: Verify thinking events are created

#### `TestCollectStreamToResult`

- **`test_collects_content()`**:
  - **What it does**: Collects content from stream
  - **Purpose**: Verify content is accumulated correctly

- **`test_collects_tool_calls()`**:
  - **What it does**: Collects tool calls from stream
  - **Purpose**: Verify tool calls are accumulated correctly

- **`test_collects_usage()`**:
  - **What it does**: Collects usage from stream
  - **Purpose**: Verify usage is stored correctly

- **`test_collects_context_usage_percentage()`**:
  - **What it does**: Collects context usage percentage from stream
  - **Purpose**: Verify context usage is stored correctly

- **`test_collects_thinking_content()`**:
  - **What it does**: Collects thinking content from stream
  - **Purpose**: Verify thinking content is accumulated correctly

- **`test_deduplicates_bracket_tool_calls()`**:
  - **What it does**: Deduplicates bracket-style tool calls
  - **Purpose**: Verify duplicate tool calls are removed

#### `TestCalculateTokensFromContextUsage`

- **`test_calculates_tokens_from_percentage()`**:
  - **What it does**: Calculates tokens from context usage percentage
  - **Purpose**: Verify token calculation is correct

- **`test_handles_zero_percentage()`**:
  - **What it does**: Handles zero context usage percentage
  - **Purpose**: Verify fallback behavior for zero percentage

- **`test_handles_none_percentage()`**:
  - **What it does**: Handles None context usage percentage
  - **Purpose**: Verify fallback behavior for None percentage

- **`test_prevents_negative_prompt_tokens()`**:
  - **What it does**: Prevents negative prompt tokens
  - **Purpose**: Verify prompt_tokens is never negative

- **`test_uses_model_specific_max_tokens()`**:
  - **What it does**: Uses model-specific max input tokens
  - **Purpose**: Verify model cache is queried correctly

- **`test_small_percentage_calculation()`**:
  - **What it does**: Calculates tokens for small percentage
  - **Purpose**: Verify precision for small percentages

- **`test_large_percentage_calculation()`**:
  - **What it does**: Calculates tokens for large percentage
  - **Purpose**: Verify calculation for high context usage

#### `TestThinkingParserIntegration`

- **`test_thinking_parser_enabled_when_fake_reasoning_on()`**:
  - **What it does**: Enables thinking parser when FAKE_REASONING_ENABLED is True
  - **Purpose**: Verify thinking parser is created

- **`test_thinking_parser_disabled_when_fake_reasoning_off()`**:
  - **What it does**: Disables thinking parser when FAKE_REASONING_ENABLED is False
  - **Purpose**: Verify thinking parser is not created

- **`test_thinking_parser_can_be_disabled_via_parameter()`**:
  - **What it does**: Disables thinking parser via enable_thinking_parser parameter
  - **Purpose**: Verify parameter overrides config

#### `TestStreamingCoreErrorHandling`

- **`test_propagates_first_token_timeout_error()`**:
  - **What it does**: Propagates FirstTokenTimeoutError
  - **Purpose**: Verify timeout error is not caught internally

- **`test_propagates_generator_exit()`**:
  - **What it does**: Propagates GeneratorExit
  - **Purpose**: Verify client disconnect is handled

- **`test_propagates_other_exceptions()`**:
  - **What it does**: Propagates other exceptions
  - **Purpose**: Verify errors are not swallowed

#### `TestStreamWithFirstTokenRetryCore`

Tests for stream_with_first_token_retry() generic function that provides automatic retry logic on first token timeout. Used by both OpenAI and Anthropic streaming implementations.

- **`test_yields_chunks_on_success()`**:
  - **What it does**: Yields chunks on successful streaming
  - **Purpose**: Verify normal operation without retries

- **`test_retries_on_first_token_timeout()`**:
  - **What it does**: Retries on first token timeout
  - **Purpose**: Verify retry logic is triggered

- **`test_raises_exception_after_all_retries()`**:
  - **What it does**: Raises exception after all retries exhausted
  - **Purpose**: Verify error handling when all retries fail

- **`test_uses_custom_error_callbacks()`**:
  - **What it does**: Uses custom error callbacks
  - **Purpose**: Verify on_http_error and on_all_retries_failed callbacks

- **`test_handles_http_error()`**:
  - **What it does**: Handles HTTP error from API
  - **Purpose**: Verify HTTP errors are handled correctly

- **`test_uses_custom_http_error_callback()`**:
  - **What it does**: Uses custom HTTP error callback
  - **Purpose**: Verify on_http_error callback is used

- **`test_closes_response_on_timeout()`**:
  - **What it does**: Closes response on timeout
  - **Purpose**: Verify response is properly closed after timeout

- **`test_propagates_non_timeout_exceptions()`**:
  - **What it does**: Propagates non-timeout exceptions without retry
  - **Purpose**: Verify other exceptions are not retried

- **`test_uses_configured_max_retries()`**:
  - **What it does**: Uses configured max_retries value
  - **Purpose**: Verify max_retries parameter is respected

- **`test_multiple_retries_then_success()`**:
  - **What it does**: Succeeds after multiple retries
  - **Purpose**: Verify recovery after multiple failures

- **`test_closes_response_on_http_error()`**:
  - **What it does**: Closes response on HTTP error
  - **Purpose**: Verify response is properly closed after HTTP error

---

### `tests/unit/test_streaming_openai.py`

Unit tests for **OpenAI streaming module** (Kiro → OpenAI SSE format conversion). **36 tests.**

#### `TestStreamKiroToOpenai`

- **`test_yields_content_chunks()`**:
  - **What it does**: Yields content chunks in OpenAI format
  - **Purpose**: Verify content streaming

- **`test_first_chunk_has_role()`**:
  - **What it does**: First chunk includes role: assistant
  - **Purpose**: Verify OpenAI streaming protocol

- **`test_yields_done_at_end()`**:
  - **What it does**: Yields [DONE] at end of stream
  - **Purpose**: Verify stream termination

- **`test_yields_final_chunk_with_usage()`**:
  - **What it does**: Yields final chunk with usage info
  - **Purpose**: Verify usage is included

- **`test_yields_tool_calls_chunk()`**:
  - **What it does**: Yields tool_calls chunk when tools present
  - **Purpose**: Verify tool call streaming

- **`test_tool_calls_have_index()`**:
  - **What it does**: Tool calls have index field
  - **Purpose**: Verify OpenAI streaming spec compliance

- **`test_finish_reason_is_tool_calls_when_tools_present()`**:
  - **What it does**: Sets finish_reason to tool_calls when tools present
  - **Purpose**: Verify correct finish reason

- **`test_finish_reason_is_stop_without_tools()`**:
  - **What it does**: Sets finish_reason to stop without tools
  - **Purpose**: Verify correct finish reason

- **`test_closes_response_on_completion()`**:
  - **What it does**: Closes response on completion
  - **Purpose**: Verify resource cleanup

- **`test_closes_response_on_error()`**:
  - **What it does**: Closes response on error
  - **Purpose**: Verify resource cleanup on error

#### `TestStreamingOpenaiThinkingContent`

- **`test_yields_thinking_as_reasoning_content()`**:
  - **What it does**: Yields thinking as reasoning_content when configured
  - **Purpose**: Verify thinking content handling

- **`test_yields_thinking_as_content_when_configured()`**:
  - **What it does**: Yields thinking as content when configured
  - **Purpose**: Verify thinking content handling

#### `TestStreamingOpenaiNoneProtection`

- **`test_handles_none_function_name()`**:
  - **What it does**: Handles None in function.name
  - **Purpose**: Verify None is replaced with empty string

- **`test_handles_none_function_arguments()`**:
  - **What it does**: Handles None in function.arguments
  - **Purpose**: Verify None is replaced with "{}"

- **`test_handles_none_function_object()`**:
  - **What it does**: Handles None function object
  - **Purpose**: Verify None function is handled

#### `TestStreamWithFirstTokenRetry`

- **`test_retries_on_first_token_timeout()`**:
  - **What it does**: Retries on first token timeout
  - **Purpose**: Verify retry logic

- **`test_raises_504_after_all_retries_exhausted()`**:
  - **What it does**: Raises 504 after all retries exhausted
  - **Purpose**: Verify error handling

- **`test_handles_api_error_response()`**:
  - **What it does**: Handles API error response
  - **Purpose**: Verify error response handling

- **`test_propagates_non_timeout_errors()`**:
  - **What it does**: Propagates non-timeout errors without retry
  - **Purpose**: Verify only timeout errors trigger retry

- **`test_closes_response_on_retry()`**:
  - **What it does**: Closes response when retrying
  - **Purpose**: Verify resource cleanup on retry

#### `TestCollectStreamResponse`

- **`test_collects_content()`**:
  - **What it does**: Collects content from stream
  - **Purpose**: Verify content accumulation

- **`test_collects_reasoning_content()`**:
  - **What it does**: Collects reasoning content from stream
  - **Purpose**: Verify reasoning content accumulation

- **`test_collects_tool_calls()`**:
  - **What it does**: Collects tool calls from stream
  - **Purpose**: Verify tool call accumulation

- **`test_tool_calls_have_no_index()`**:
  - **What it does**: Collected tool calls don't have index field
  - **Purpose**: Verify index is removed for non-streaming

- **`test_includes_usage()`**:
  - **What it does**: Includes usage in response
  - **Purpose**: Verify usage is included

- **`test_sets_finish_reason_tool_calls()`**:
  - **What it does**: Sets finish_reason to tool_calls when tools present
  - **Purpose**: Verify correct finish reason

- **`test_sets_finish_reason_stop()`**:
  - **What it does**: Sets finish_reason to stop without tools
  - **Purpose**: Verify correct finish reason

- **`test_generates_completion_id()`**:
  - **What it does**: Generates completion ID
  - **Purpose**: Verify ID is present

- **`test_includes_model_name()`**:
  - **What it does**: Includes model name in response
  - **Purpose**: Verify model is included

- **`test_object_is_chat_completion()`**:
  - **What it does**: Sets object to chat.completion
  - **Purpose**: Verify OpenAI format

#### `TestStreamingOpenaiErrorHandling`

- **`test_propagates_first_token_timeout_error()`**:
  - **What it does**: Propagates FirstTokenTimeoutError
  - **Purpose**: Verify timeout error is propagated for retry

- **`test_handles_generator_exit_gracefully()`**:
  - **What it does**: Handles GeneratorExit gracefully without re-raising
  - **Purpose**: Verify client disconnect is handled without error

- **`test_propagates_other_exceptions()`**:
  - **What it does**: Propagates other exceptions
  - **Purpose**: Verify errors are not swallowed

- **`test_aclose_error_does_not_mask_original()`**:
  - **What it does**: aclose() error doesn't mask original error
  - **Purpose**: Verify original exception is propagated

#### `TestStreamingOpenaiBracketToolCalls`

- **`test_detects_bracket_tool_calls()`**:
  - **What it does**: Detects bracket-style tool calls in content
  - **Purpose**: Verify bracket tool call detection

- **`test_deduplicates_tool_calls()`**:
  - **What it does**: Deduplicates tool calls from stream and bracket
  - **Purpose**: Verify deduplication

#### `TestStreamingOpenaiMeteringData`

- **`test_includes_credits_used_in_usage()`**:
  - **What it does**: Includes credits_used in usage when metering data present
  - **Purpose**: Verify metering data is included

---

### `tests/unit/test_http_client.py`

Unit tests for **KiroHttpClient** (HTTP client with retry logic). **29 tests.**

#### `TestKiroHttpClientInitialization`

- **`test_initialization_stores_auth_manager()`**: Verifies auth_manager storage during initialization
- **`test_initialization_client_is_none()`**: Verifies that HTTP client is initially None

#### `TestKiroHttpClientGetClient`

- **`test_get_client_creates_new_client()`**: Verifies new HTTP client creation
- **`test_get_client_reuses_existing_client()`**: Verifies existing client reuse
- **`test_get_client_recreates_closed_client()`**: Verifies closed client recreation

#### `TestKiroHttpClientClose`

- **`test_close_closes_client()`**: Verifies HTTP client closing
- **`test_close_does_nothing_for_none_client()`**: Verifies close() doesn't crash for None client
- **`test_close_does_nothing_for_closed_client()`**: Verifies close() doesn't crash for closed client

#### `TestKiroHttpClientRequestWithRetry`

- **`test_successful_request_returns_response()`**: Verifies successful request
- **`test_403_triggers_token_refresh()`**: Verifies token refresh on 403
- **`test_429_triggers_backoff()`**: Verifies exponential backoff on 429
- **`test_5xx_triggers_backoff()`**: Verifies exponential backoff on 5xx
- **`test_timeout_triggers_backoff()`**: Verifies exponential backoff on timeout
- **`test_request_error_triggers_backoff()`**: Verifies exponential backoff on request error
- **`test_max_retries_exceeded_raises_502()`**: Verifies HTTPException after retries exhausted
- **`test_other_status_codes_returned_as_is()`**: Verifies other status codes return without retry
- **`test_streaming_request_uses_send()`**: Verifies send() usage for streaming

#### `TestKiroHttpClientContextManager`

- **`test_context_manager_returns_self()`**: Verifies __aenter__ returns self
- **`test_context_manager_closes_on_exit()`**: Verifies client closing on context exit

#### `TestKiroHttpClientExponentialBackoff`

- **`test_backoff_delay_increases_exponentially()`**: Verifies exponential delay increase

#### `TestKiroHttpClientStreamingTimeout`

Tests for streaming timeout logic (httpx timeouts, not FIRST_TOKEN_TIMEOUT).

- **`test_streaming_uses_streaming_read_timeout()`**:
  - **What it does**: Verifies that streaming requests use STREAMING_READ_TIMEOUT for read timeout
  - **Purpose**: Ensure httpx.Timeout is configured with connect=30s and read=STREAMING_READ_TIMEOUT

- **`test_streaming_uses_first_token_max_retries()`**:
  - **What it does**: Verifies that streaming requests use FIRST_TOKEN_MAX_RETRIES
  - **Purpose**: Ensure separate retry counter is used for stream=True

- **`test_streaming_timeout_retry_without_delay()`**:
  - **What it does**: Verifies that streaming timeout retry happens without delay
  - **Purpose**: Ensure no exponential backoff on streaming timeout

- **`test_non_streaming_uses_default_timeout()`**:
  - **What it does**: Verifies that non-streaming requests use httpx.Timeout(timeout=300)
  - **Purpose**: Ensure unified 300s timeout for all operations in non-streaming mode

- **`test_connect_timeout_logged_correctly()`**:
  - **What it does**: Verifies that ConnectTimeout is logged with [ConnectTimeout] prefix
  - **Purpose**: Ensure timeout type is visible in logs for debugging

- **`test_read_timeout_logged_correctly()`**:
  - **What it does**: Verifies that ReadTimeout is logged with [ReadTimeout] prefix and STREAMING_READ_TIMEOUT value
  - **Purpose**: Ensure timeout type and value are visible in logs

- **`test_streaming_timeout_returns_504_with_error_type()`**:
  - **What it does**: Verifies that streaming timeout returns 504 with error type in detail
  - **Purpose**: Ensure 504 Gateway Timeout includes error type (e.g., "ReadTimeout")

- **`test_non_streaming_timeout_returns_502()`**:
  - **What it does**: Verifies that non-streaming timeout returns 502
  - **Purpose**: Ensure old logic with 502 is used for non-streaming

#### `TestKiroHttpClientSharedClient`

Tests for shared client functionality (connection pooling support, fix for issue #24).

- **`test_initialization_with_shared_client()`**:
  - **What it does**: Verifies shared_client is stored during initialization
  - **Purpose**: Ensure shared client is available for connection pooling

- **`test_initialization_without_shared_client_owns_client()`**:
  - **What it does**: Verifies _owns_client is True when no shared client provided
  - **Purpose**: Ensure client ownership is tracked correctly for cleanup

- **`test_initialization_with_shared_client_does_not_own()`**:
  - **What it does**: Verifies _owns_client is False when shared client provided
  - **Purpose**: Ensure shared client is not closed by this instance

- **`test_get_client_returns_shared_client()`**:
  - **What it does**: Verifies _get_client returns shared client directly
  - **Purpose**: Ensure shared client is used without creating new one

- **`test_close_does_not_close_shared_client()`**:
  - **What it does**: Verifies close() does NOT close shared client
  - **Purpose**: Ensure shared client lifecycle is managed by application

- **`test_close_closes_owned_client()`**:
  - **What it does**: Verifies close() DOES close owned client
  - **Purpose**: Ensure owned client is properly cleaned up

#### `TestKiroHttpClientGracefulClose`

Tests for graceful exception handling in close() method.

- **`test_close_handles_aclose_exception_gracefully()`**:
  - **What it does**: Verifies exception in aclose() is caught and doesn't propagate
  - **Purpose**: Ensure cleanup errors don't mask original exceptions

- **`test_close_logs_warning_on_exception()`**:
  - **What it does**: Verifies warning is logged when aclose() fails
  - **Purpose**: Ensure errors are visible in logs for debugging

---

### `tests/unit/test_routes_anthropic.py`

Unit tests for **Anthropic API endpoints** (/v1/messages). **44 tests.**

#### `TestVerifyAnthropicApiKey`

- **`test_valid_x_api_key_returns_true()`**:
  - **What it does**: Verifies that a valid x-api-key header passes authentication
  - **Purpose**: Ensure Anthropic native authentication works

- **`test_valid_bearer_token_returns_true()`**:
  - **What it does**: Verifies that a valid Bearer token passes authentication
  - **Purpose**: Ensure OpenAI-style authentication also works

- **`test_x_api_key_takes_precedence()`**:
  - **What it does**: Verifies x-api-key is checked before Authorization header
  - **Purpose**: Ensure Anthropic native auth has priority

- **`test_invalid_x_api_key_raises_401()`**:
  - **What it does**: Verifies that an invalid x-api-key is rejected
  - **Purpose**: Ensure unauthorized access is blocked

- **`test_invalid_bearer_token_raises_401()`**:
  - **What it does**: Verifies that an invalid Bearer token is rejected
  - **Purpose**: Ensure unauthorized access is blocked

- **`test_missing_both_headers_raises_401()`**:
  - **What it does**: Verifies that missing both headers is rejected
  - **Purpose**: Ensure authentication is required

- **`test_empty_x_api_key_raises_401()`**:
  - **What it does**: Verifies that empty x-api-key is rejected
  - **Purpose**: Ensure empty credentials are blocked

- **`test_error_response_format_is_anthropic_style()`**:
  - **What it does**: Verifies error response follows Anthropic format
  - **Purpose**: Ensure error format matches Anthropic API

#### `TestMessagesAuthentication`

- **`test_messages_requires_authentication()`**:
  - **What it does**: Verifies messages endpoint requires authentication
  - **Purpose**: Ensure protected endpoint is secured

- **`test_messages_accepts_x_api_key()`**:
  - **What it does**: Verifies messages endpoint accepts x-api-key header
  - **Purpose**: Ensure Anthropic native authentication works

- **`test_messages_accepts_bearer_token()`**:
  - **What it does**: Verifies messages endpoint accepts Bearer token
  - **Purpose**: Ensure OpenAI-style authentication also works

- **`test_messages_rejects_invalid_x_api_key()`**:
  - **What it does**: Verifies messages endpoint rejects invalid x-api-key
  - **Purpose**: Ensure authentication is enforced

#### `TestMessagesValidation`

- **`test_validates_missing_model()`**:
  - **What it does**: Verifies missing model field is rejected
  - **Purpose**: Ensure model is required

- **`test_validates_missing_max_tokens()`**:
  - **What it does**: Verifies missing max_tokens field is rejected
  - **Purpose**: Ensure max_tokens is required (Anthropic API requirement)

- **`test_validates_missing_messages()`**:
  - **What it does**: Verifies missing messages field is rejected
  - **Purpose**: Ensure messages are required

- **`test_validates_empty_messages_array()`**:
  - **What it does**: Verifies empty messages array is rejected
  - **Purpose**: Ensure at least one message is required

- **`test_validates_invalid_json()`**:
  - **What it does**: Verifies invalid JSON is rejected
  - **Purpose**: Ensure proper JSON parsing

- **`test_validates_invalid_role()`**:
  - **What it does**: Verifies invalid message role is rejected
  - **Purpose**: Anthropic model strictly validates role (only 'user' or 'assistant')

- **`test_accepts_valid_request_format()`**:
  - **What it does**: Verifies valid request format passes validation
  - **Purpose**: Ensure Pydantic validation works correctly

#### `TestMessagesSystemPrompt`

- **`test_accepts_system_as_separate_field()`**:
  - **What it does**: Verifies system prompt as separate field is accepted
  - **Purpose**: Ensure Anthropic-style system prompt works

- **`test_accepts_empty_system_prompt()`**:
  - **What it does**: Verifies empty system prompt is accepted
  - **Purpose**: Ensure system prompt is optional

- **`test_accepts_no_system_prompt()`**:
  - **What it does**: Verifies request without system prompt is accepted
  - **Purpose**: Ensure system prompt is optional

#### `TestMessagesContentBlocks`

- **`test_accepts_string_content()`**:
  - **What it does**: Verifies string content is accepted
  - **Purpose**: Ensure simple string content works

- **`test_accepts_content_block_array()`**:
  - **What it does**: Verifies content block array is accepted
  - **Purpose**: Ensure Anthropic content block format works

- **`test_accepts_multiple_content_blocks()`**:
  - **What it does**: Verifies multiple content blocks are accepted
  - **Purpose**: Ensure complex content works

#### `TestMessagesToolUse`

- **`test_accepts_tool_definition()`**:
  - **What it does**: Verifies tool definition is accepted
  - **Purpose**: Ensure Anthropic tool format works

- **`test_accepts_multiple_tools()`**:
  - **What it does**: Verifies multiple tools are accepted
  - **Purpose**: Ensure multiple tool definitions work

- **`test_accepts_tool_result_message()`**:
  - **What it does**: Verifies tool result message is accepted
  - **Purpose**: Ensure tool result handling works

#### `TestMessagesOptionalParams`

- **`test_accepts_temperature_parameter()`**:
  - **What it does**: Verifies temperature parameter is accepted
  - **Purpose**: Ensure temperature control works

- **`test_accepts_top_p_parameter()`**:
  - **What it does**: Verifies top_p parameter is accepted
  - **Purpose**: Ensure nucleus sampling control works

- **`test_accepts_top_k_parameter()`**:
  - **What it does**: Verifies top_k parameter is accepted
  - **Purpose**: Ensure top-k sampling control works

- **`test_accepts_stream_true()`**:
  - **What it does**: Verifies stream=true is accepted
  - **Purpose**: Ensure streaming mode is supported

- **`test_accepts_stop_sequences()`**:
  - **What it does**: Verifies stop_sequences parameter is accepted
  - **Purpose**: Ensure stop sequence control works

- **`test_accepts_metadata()`**:
  - **What it does**: Verifies metadata parameter is accepted
  - **Purpose**: Ensure metadata passing works

#### `TestMessagesAnthropicVersion`

- **`test_accepts_anthropic_version_header()`**:
  - **What it does**: Verifies anthropic-version header is accepted
  - **Purpose**: Ensure Anthropic SDK compatibility

- **`test_works_without_anthropic_version_header()`**:
  - **What it does**: Verifies request works without anthropic-version header
  - **Purpose**: Ensure header is optional

#### `TestAnthropicRouterIntegration`

- **`test_router_has_messages_endpoint()`**:
  - **What it does**: Verifies messages endpoint is registered
  - **Purpose**: Ensure endpoint is available

- **`test_messages_endpoint_uses_post_method()`**:
  - **What it does**: Verifies messages endpoint uses POST method
  - **Purpose**: Ensure correct HTTP method

- **`test_router_has_anthropic_tag()`**:
  - **What it does**: Verifies router has Anthropic API tag
  - **Purpose**: Ensure proper API documentation grouping

#### `TestMessagesConversationHistory`

- **`test_accepts_multi_turn_conversation()`**:
  - **What it does**: Verifies multi-turn conversation is accepted
  - **Purpose**: Ensure conversation history works

- **`test_accepts_long_conversation()`**:
  - **What it does**: Verifies long conversation is accepted
  - **Purpose**: Ensure many messages work

#### `TestMessagesErrorFormat`

- **`test_validation_error_format()`**:
  - **What it does**: Verifies validation error response format
  - **Purpose**: Ensure errors follow expected format

- **`test_auth_error_format_is_anthropic_style()`**:
  - **What it does**: Verifies auth error follows Anthropic format
  - **Purpose**: Ensure error format matches Anthropic API

---

### `tests/unit/test_routes_openai.py`

Unit tests for **OpenAI API endpoints** (/, /health, /v1/models, /v1/chat/completions). **46 tests.**

#### `TestVerifyApiKey`

- **`test_valid_bearer_token_returns_true()`**:
  - **What it does**: Verifies that a valid Bearer token passes authentication
  - **Purpose**: Ensure correct API keys are accepted

- **`test_invalid_api_key_raises_401()`**:
  - **What it does**: Verifies that an invalid API key is rejected
  - **Purpose**: Ensure unauthorized access is blocked

- **`test_missing_api_key_raises_401()`**:
  - **What it does**: Verifies that missing API key is rejected
  - **Purpose**: Ensure requests without authentication are blocked

- **`test_empty_api_key_raises_401()`**:
  - **What it does**: Verifies that empty string API key is rejected
  - **Purpose**: Ensure empty credentials are blocked

- **`test_key_without_bearer_prefix_raises_401()`**:
  - **What it does**: Verifies that API key without Bearer prefix is rejected
  - **Purpose**: Ensure proper Authorization header format is required

- **`test_bearer_with_extra_spaces_raises_401()`**:
  - **What it does**: Verifies that Bearer token with extra spaces is rejected
  - **Purpose**: Ensure strict format validation

- **`test_lowercase_bearer_raises_401()`**:
  - **What it does**: Verifies that lowercase 'bearer' is rejected
  - **Purpose**: Ensure case-sensitive Bearer prefix

#### `TestRootEndpoint`

- **`test_root_returns_status_ok()`**:
  - **What it does**: Verifies root endpoint returns ok status
  - **Purpose**: Ensure basic health check works

- **`test_root_returns_gateway_message()`**:
  - **What it does**: Verifies root endpoint returns gateway message
  - **Purpose**: Ensure service identification is present

- **`test_root_returns_version()`**:
  - **What it does**: Verifies root endpoint returns application version
  - **Purpose**: Ensure version information is available

- **`test_root_does_not_require_auth()`**:
  - **What it does**: Verifies root endpoint is accessible without authentication
  - **Purpose**: Ensure public health check availability

#### `TestHealthEndpoint`

- **`test_health_returns_healthy_status()`**:
  - **What it does**: Verifies health endpoint returns healthy status
  - **Purpose**: Ensure health check indicates service is running

- **`test_health_returns_timestamp()`**:
  - **What it does**: Verifies health endpoint returns timestamp
  - **Purpose**: Ensure timestamp is present for monitoring

- **`test_health_returns_version()`**:
  - **What it does**: Verifies health endpoint returns version
  - **Purpose**: Ensure version is available for monitoring

- **`test_health_does_not_require_auth()`**:
  - **What it does**: Verifies health endpoint is accessible without authentication
  - **Purpose**: Ensure health checks work for load balancers

#### `TestModelsEndpoint`

- **`test_models_requires_authentication()`**:
  - **What it does**: Verifies models endpoint requires authentication
  - **Purpose**: Ensure protected endpoints are secured

- **`test_models_rejects_invalid_key()`**:
  - **What it does**: Verifies models endpoint rejects invalid API key
  - **Purpose**: Ensure authentication is enforced

- **`test_models_returns_list_object()`**:
  - **What it does**: Verifies models endpoint returns list object type
  - **Purpose**: Ensure OpenAI API compatibility

- **`test_models_returns_data_array()`**:
  - **What it does**: Verifies models endpoint returns data array
  - **Purpose**: Ensure response structure matches OpenAI format

- **`test_models_contains_available_models()`**:
  - **What it does**: Verifies all configured models are returned
  - **Purpose**: Ensure model list is complete

- **`test_models_format_is_openai_compatible()`**:
  - **What it does**: Verifies model objects have OpenAI-compatible format
  - **Purpose**: Ensure compatibility with OpenAI clients

- **`test_models_owned_by_anthropic()`**:
  - **What it does**: Verifies models are owned by Anthropic
  - **Purpose**: Ensure correct model attribution

#### `TestChatCompletionsAuthentication`

- **`test_chat_completions_requires_authentication()`**:
  - **What it does**: Verifies chat completions requires authentication
  - **Purpose**: Ensure protected endpoint is secured

- **`test_chat_completions_rejects_invalid_key()`**:
  - **What it does**: Verifies chat completions rejects invalid API key
  - **Purpose**: Ensure authentication is enforced

#### `TestChatCompletionsValidation`

- **`test_validates_empty_messages_array()`**:
  - **What it does**: Verifies empty messages array is rejected
  - **Purpose**: Ensure at least one message is required

- **`test_validates_missing_model()`**:
  - **What it does**: Verifies missing model field is rejected
  - **Purpose**: Ensure model is required

- **`test_validates_missing_messages()`**:
  - **What it does**: Verifies missing messages field is rejected
  - **Purpose**: Ensure messages are required

- **`test_validates_invalid_json()`**:
  - **What it does**: Verifies invalid JSON is rejected
  - **Purpose**: Ensure proper JSON parsing

- **`test_validates_invalid_role()`**:
  - **What it does**: Verifies invalid message role passes Pydantic validation
  - **Purpose**: Pydantic model accepts any string as role (validation happens later)

- **`test_accepts_valid_request_format()`**:
  - **What it does**: Verifies valid request format passes validation
  - **Purpose**: Ensure Pydantic validation works correctly

- **`test_accepts_message_without_content()`**:
  - **What it does**: Verifies message without content is accepted
  - **Purpose**: Ensure content is optional (for tool results)

#### `TestChatCompletionsWithTools`

- **`test_accepts_valid_tool_definition()`**:
  - **What it does**: Verifies valid tool definition is accepted
  - **Purpose**: Ensure tool calling format is supported

- **`test_accepts_multiple_tools()`**:
  - **What it does**: Verifies multiple tools are accepted
  - **Purpose**: Ensure multiple tool definitions work

#### `TestChatCompletionsOptionalParams`

- **`test_accepts_temperature_parameter()`**:
  - **What it does**: Verifies temperature parameter is accepted
  - **Purpose**: Ensure temperature control works

- **`test_accepts_max_tokens_parameter()`**:
  - **What it does**: Verifies max_tokens parameter is accepted
  - **Purpose**: Ensure output length control works

- **`test_accepts_stream_true()`**:
  - **What it does**: Verifies stream=true is accepted
  - **Purpose**: Ensure streaming mode is supported

- **`test_accepts_top_p_parameter()`**:
  - **What it does**: Verifies top_p parameter is accepted
  - **Purpose**: Ensure nucleus sampling control works

#### `TestChatCompletionsMessageTypes`

- **`test_accepts_system_message()`**:
  - **What it does**: Verifies system message is accepted
  - **Purpose**: Ensure system prompts work

- **`test_accepts_assistant_message()`**:
  - **What it does**: Verifies assistant message is accepted
  - **Purpose**: Ensure conversation history works

- **`test_accepts_multipart_content()`**:
  - **What it does**: Verifies multipart content array is accepted
  - **Purpose**: Ensure complex content format works

#### `TestRouterIntegration`

- **`test_router_has_root_endpoint()`**:
  - **What it does**: Verifies root endpoint is registered
  - **Purpose**: Ensure endpoint is available

- **`test_router_has_health_endpoint()`**:
  - **What it does**: Verifies health endpoint is registered
  - **Purpose**: Ensure endpoint is available

- **`test_router_has_models_endpoint()`**:
  - **What it does**: Verifies models endpoint is registered
  - **Purpose**: Ensure endpoint is available

- **`test_router_has_chat_completions_endpoint()`**:
  - **What it does**: Verifies chat completions endpoint is registered
  - **Purpose**: Ensure endpoint is available

- **`test_root_endpoint_uses_get_method()`**:
  - **What it does**: Verifies root endpoint uses GET method
  - **Purpose**: Ensure correct HTTP method

- **`test_health_endpoint_uses_get_method()`**:
  - **What it does**: Verifies health endpoint uses GET method
  - **Purpose**: Ensure correct HTTP method

- **`test_models_endpoint_uses_get_method()`**:
  - **What it does**: Verifies models endpoint uses GET method
  - **Purpose**: Ensure correct HTTP method

- **`test_chat_completions_endpoint_uses_post_method()`**:
  - **What it does**: Verifies chat completions endpoint uses POST method
  - **Purpose**: Ensure correct HTTP method

---

### `tests/unit/test_main_cli.py`

Unit tests for **main.py CLI functions** (command-line argument parsing and server configuration). **17 tests.**

#### `TestParseCliArgs`

Tests for parse_cli_args() function.

- **`test_default_values_are_none()`**:
  - **What it does**: Verifies that default values for host and port are None
  - **Purpose**: Ensure that None indicates "use env or default" in priority resolution

- **`test_port_argument_long_form()`**:
  - **What it does**: Verifies that --port argument is parsed correctly
  - **Purpose**: Ensure long form --port works

- **`test_port_argument_short_form()`**:
  - **What it does**: Verifies that -p argument is parsed correctly
  - **Purpose**: Ensure short form -p works

- **`test_host_argument_long_form()`**:
  - **What it does**: Verifies that --host argument is parsed correctly
  - **Purpose**: Ensure long form --host works

- **`test_host_argument_short_form()`**:
  - **What it does**: Verifies that -H argument is parsed correctly
  - **Purpose**: Ensure short form -H works

- **`test_both_arguments_together()`**:
  - **What it does**: Verifies that both --host and --port can be used together
  - **Purpose**: Ensure both arguments work simultaneously

- **`test_short_forms_together()`**:
  - **What it does**: Verifies that both -H and -p can be used together
  - **Purpose**: Ensure short forms work simultaneously

#### `TestResolveServerConfig`

Tests for resolve_server_config() function - priority hierarchy.

- **`test_cli_args_take_priority_over_env()`**:
  - **What it does**: Verifies that CLI arguments have highest priority
  - **Purpose**: Ensure CLI args override environment variables

- **`test_env_vars_take_priority_over_defaults()`**:
  - **What it does**: Verifies that env vars have priority over defaults
  - **Purpose**: Ensure env vars are used when CLI args are not provided

- **`test_defaults_used_when_nothing_set()`**:
  - **What it does**: Verifies that defaults are used when nothing else is set
  - **Purpose**: Ensure default values work correctly

- **`test_cli_host_only_env_port()`**:
  - **What it does**: Verifies mixed priority - CLI host with env port
  - **Purpose**: Ensure each argument is resolved independently

- **`test_cli_port_only_env_host()`**:
  - **What it does**: Verifies mixed priority - CLI port with env host
  - **Purpose**: Ensure each argument is resolved independently

#### `TestPrintStartupBanner`

Tests for print_startup_banner() function.

- **`test_banner_contains_url()`**:
  - **What it does**: Verifies that banner contains the server URL
  - **Purpose**: Ensure URL is displayed to user

- **`test_banner_contains_custom_port()`**:
  - **What it does**: Verifies that banner shows custom port
  - **Purpose**: Ensure custom port is displayed correctly

- **`test_banner_contains_docs_url()`**:
  - **What it does**: Verifies that banner contains API docs URL
  - **Purpose**: Ensure /docs endpoint is mentioned

- **`test_banner_contains_health_url()`**:
  - **What it does**: Verifies that banner contains health check URL
  - **Purpose**: Ensure /health endpoint is mentioned

#### `TestCliHelp`

Tests for CLI help output.

- **`test_help_shows_port_option()`**:
  - **What it does**: Verifies that --help shows port option
  - **Purpose**: Ensure help is informative

- **`test_help_shows_host_option()`**:
  - **What it does**: Verifies that --help output contains host option
  - **Purpose**: Ensure host option is documented

#### `TestCliVersion`

Tests for CLI version output.

- **`test_version_flag_exits_with_zero()`**:
  - **What it does**: Verifies that --version exits with code 0
  - **Purpose**: Ensure version flag works correctly

- **`test_version_shows_app_version()`**:
  - **What it does**: Verifies that --version shows application version
  - **Purpose**: Ensure version is displayed

---

### `tests/integration/test_full_flow.py`

Integration tests for **full end-to-end flow**. **12 tests (11 passed, 1 skipped).**

#### `TestFullChatCompletionFlow`

- **`test_full_flow_health_to_models_to_chat()`**: Verifies full flow from health check to chat completions
- **`test_authentication_flow()`**: Verifies authentication flow
- **`test_openai_compatibility_format()`**: Verifies response format compatibility with OpenAI API

#### `TestRequestValidationFlow`

- **`test_chat_completions_request_validation()`**: Verifies various request format validation
- **`test_complex_message_formats()`**: Verifies complex message format handling

#### `TestErrorHandlingFlow`

- **`test_invalid_json_handling()`**: Verifies invalid JSON handling
- **`test_wrong_content_type_handling()`**: SKIPPED - bug discovered in validation_exception_handler

#### `TestModelsEndpointIntegration`

- **`test_models_returns_all_available_models()`**: Verifies all models from config are returned
- **`test_models_caching_behavior()`**: Verifies model caching behavior

#### `TestStreamingFlagHandling`

- **`test_stream_true_accepted()`**: Verifies stream=true acceptance
- **`test_stream_false_accepted()`**: Verifies stream=false acceptance

#### `TestHealthEndpointIntegration`

- **`test_root_and_health_consistency()`**: Verifies / and /health consistency

---

## Testing Philosophy

### Principles

1. **Isolation**: Each test is completely isolated from external services through mocks
2. **Detail**: Abundant print() for understanding test flow during debugging
3. **Coverage**: Tests cover not only happy path, but also edge cases and errors
4. **Security**: All tests use mock credentials, never real ones

### Test Structure (Arrange-Act-Assert)

Each test follows the pattern:
1. **Arrange** (Setup): Prepare mocks and data
2. **Act** (Action): Execute the tested action
3. **Assert** (Verify): Verify result with explicit comparison

### Test Types

- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Verify component interactions
- **Security tests**: Verify security system
- **Edge case tests**: Paranoid edge case checks

## Adding New Tests

When adding new tests:

1. Follow existing class structure (`Test*Success`, `Test*Errors`, `Test*EdgeCases`)
2. Use descriptive names: `test_<what_it_does>_<expected_result>`
3. Add docstring with "What it does" and "Purpose"
4. Use print() for logging test steps
5. Update this README with new test description

## Troubleshooting

### Tests fail with ImportError

```bash
# Make sure you're in project root
cd /path/to/kiro-gateway

# pytest.ini already contains pythonpath = .
# Just run pytest
pytest
```

### Tests pass locally but fail in CI

- Check dependency versions in requirements.txt
- Ensure all mocks correctly isolate external calls

### Async tests don't work

```bash
# Make sure pytest-asyncio is installed
pip install pytest-asyncio

# Check for @pytest.mark.asyncio decorator
```

## Coverage Metrics

To check code coverage:

```bash
# Install coverage
pip install pytest-cov

# Run with coverage report
pytest --cov=kiro --cov-report=html

# View report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## Contacts and Support

If you find bugs or have suggestions for test improvements, create an issue in the project repository.
