# Сценарий: n8n в облаке, MCP/Dashboard/logs локально

> **Когда читать.** Если ваш n8n работает в облаке (n8n.cloud, self-hosted удалённо, на VPS), а MCP-сервер из M3, Dashboard из M4 и/или `logs.json` для WF2 крутятся у вас локально на `localhost`. n8n из облака не может достучаться до `localhost` — нужен публичный HTTPS-туннель.
>
> Если у вас n8n self-host **на том же ноуте**, где запущены MCP/backend/logs — этот гайд можно пропустить. n8n self-host локально ходит на `http://localhost:7777/mcp` / `http://host.docker.internal:7777/mcp` без туннелей.

---

## Зачем туннель — суть проблемы

```
[ваш ноут]                                      [n8n cloud]
  ├─ mcp-features    :7777   ←─── ✗ не достучаться (приватный IP)
  ├─ backend         :5001                              │
  └─ logs.json server :8080  ←─── ✗ не достучаться      │
                                                         ▼
                                              WF2 → GET /logs.json (HTTP)
                                              AI Agent → MCP Client Tool
```

Облачный n8n не видит ваш `localhost`. Решение — публичный HTTPS-эндпойнт перед локальным сервисом. Самый быстрый вариант — **Cloudflare quick tunnel**.

### Почему Cloudflare quick tunnel

- **Бесплатно, ноль конфигурации.** Не нужен аккаунт Cloudflare, не нужна верификация домена.
- **HTTPS из коробки.** Cloudflare сам выдаёт TLS-сертификат на эфемерный поддомен `*.trycloudflare.com`.
- **Один Docker-сервис.** Образ `cloudflare/cloudflared:latest`, команда `tunnel --url http://<сервис>:<порт>`.
- **Работает на любом сетевом окружении.** За корпоративным NAT, мобильным интернетом, любым firewall.

⚠️ **Caveat — URL эфемерный.** Quick tunnel генерит новый случайный поддомен **при каждом запуске контейнера** (`cloudflare/cloudflared`). После `docker compose restart` URL поменяется → нужно обновить значение в n8n-ноде вручную. Для постоянных URL нужен Named Tunnel (бесплатный, но требует Cloudflare-аккаунта и DNS-записи).

### Альтернативы (если Cloudflare не подходит)

| Инструмент | Плюсы | Минусы |
|---|---|---|
| **ngrok** (free tier) | известный, простой | URL эфемерный + ограничения rate, нужен аккаунт |
| **localtunnel** | npm-пакет, open source | менее стабильный, иногда падает |
| **Tailscale Funnel** | persistent URL, mesh-сеть | требует Tailscale на обеих сторонах |
| **VPS + reverse proxy** | контроль, persistent URL | дольше настраивать, $5+/мес |

Для учебной домашки M5 хватает Cloudflare quick tunnel.

---

## Минимальный пример: один сервис + туннель

Допустим, у вас MCP-сервер из M3 запускается локально через Docker на порту `7777`. Чтобы n8n cloud мог обратиться к нему через MCP Client Tool, добавьте в `docker-compose.yml` два сервиса:

```yaml
services:
  # 1. ваш MCP-сервер из M3 (Streamable HTTP transport)
  mcp-features:
    build: ./mcp-features
    ports:
      - "7777:7777"
    environment:
      - MCP_TRANSPORT=http
      - MCP_HTTP_PORT=7777
      - MCP_BEARER_TOKEN=${MCP_BEARER_TOKEN:-}  # опционально — для production включить auth
    volumes:
      - ./backend/features.json:/app/backend/features.json  # MCP пишет в backend через volume
    restart: unless-stopped

  # 2. Cloudflare tunnel перед MCP — выдаёт публичный HTTPS-URL
  mcp-tunnel:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate --url http://mcp-features:7777
    depends_on:
      - mcp-features
    restart: unless-stopped
```

Поднимаете:

```bash
docker compose up -d mcp-features mcp-tunnel
```

Через ~5 секунд узнаёте публичный URL:

```bash
docker compose logs mcp-tunnel | grep trycloudflare.com
# Пример вывода:
# 2026-01-15T12:34:56Z INF +-------------------------------------------------+
# 2026-01-15T12:34:56Z INF |  https://order-cinema-vast-function.trycloudflare.com  |
# 2026-01-15T12:34:56Z INF +-------------------------------------------------+
```

В n8n credentials → **MCP Client Tool**:

- **Server Transport:** HTTP Streamable
- **Endpoint URL:** `https://order-cinema-vast-function.trycloudflare.com/mcp` *(тот URL что в логах + суффикс `/mcp` потому что MCP-сервер слушает по этому пути)*
- **Authentication:** Bearer Token (если в `MCP_BEARER_TOKEN` положили токен — пропишите его как Bearer; если оставили пустым — auth выключен, любой запрос пройдёт)

---

## Пример с двумя сервисами: MCP + logs-server (полный для M5)

WF2 в M5 требует ещё одну публичную точку — HTTP-эндпойнт к `logs.json`, потому что облачный n8n не прочитает локальный файл. Расширяем `docker-compose.yml`:

```yaml
services:
  mcp-features:
    # ... (как выше)

  mcp-tunnel:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate --url http://mcp-features:7777
    depends_on: [mcp-features]
    restart: unless-stopped

  # 3. Простой HTTP-сервер для logs.json
  logs-server:
    image: python:3.12-alpine
    command: python3 -m http.server 8080 --directory /logs
    volumes:
      - ./homework/M5/logs.json:/logs/logs.json:ro  # read-only mount: n8n только читает
    restart: unless-stopped

  # 4. Второй Cloudflare tunnel — публичный URL для logs.json
  logs-tunnel:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate --url http://logs-server:8080
    depends_on: [logs-server]
    restart: unless-stopped
```

```bash
docker compose up -d
docker compose logs logs-tunnel | grep trycloudflare.com
# https://oxide-permits-documented-supplements.trycloudflare.com
```

В WF2 в ноде **GET Logs** (HTTP Request):

- **Method:** `GET`
- **URL:** `https://oxide-permits-documented-supplements.trycloudflare.com/logs.json` *(URL из логов + `/logs.json`)*

Симулятор `simulate_wf2.py` пишет в `homework/M5/logs.json` на вашем диске → volume mount синхронизирует в контейнер `logs-server` → Cloudflare tunnel отдаёт публично → WF2 читает через HTTP.

---

## Шаги для запуска перед демо

1. Поднять docker compose:
   ```bash
   docker compose up -d
   ```
2. Получить актуальные URL (они новые при каждом старте):
   ```bash
   docker compose logs mcp-tunnel | grep trycloudflare.com
   docker compose logs logs-tunnel | grep trycloudflare.com
   ```
3. **Вставить URL'ы** в соответствующие ноды в n8n:
   - WF1 → MCP Client → `Endpoint URL` = MCP-туннель + `/mcp`
   - WF2 → GET Logs → `URL` = logs-туннель + `/logs.json`
   - WF2 → Init MCP, Get Feature Status, MCP Client → MCP-туннель + `/mcp`
4. Перезапустить workflow (deactivate → activate), чтобы новые URL применились на активной версии.

> 💡 Можно автоматизировать шаги 2-4 одним Python-скриптом, который читает логи `docker compose`, дёргает n8n REST API (`PUT /api/v1/workflows/{id}` + activate). Подход к написанию такого скрипта — отдельная задача за рамками этого гайда; см. n8n public API docs.

---

## Security caveats

- **Cloudflare quick tunnel — публичный.** Любой, кто узнает URL, попадёт на ваш локальный сервис. Для домашки это OK (URL эфемерный и не индексируется), но для production:
  - Включите Bearer auth на MCP-сервере (`MCP_BEARER_TOKEN=<длинная_строка>`).
  - Для `logs-server` — добавьте basic auth через Caddy / nginx прокси перед `http.server` (стандартный Python `http.server` auth не поддерживает).
- **Не коммитьте секреты** в `docker-compose.yml`. Используйте `${VAR}` синтаксис и `.env` файл (а `.env` в `.gitignore`).
- **Quick tunnel ≠ production-сетап.** Для постоянных URL и SLA — Named Tunnel с Cloudflare-аккаунтом и DNS-записью (бесплатно, но 5 минут настройки).

---

## Troubleshooting

| Симптом | Причина | Что делать |
|---|---|---|
| `docker compose logs mcp-tunnel` пустой | Контейнер ещё не запустился | Подождать 5-10 сек после `docker compose up -d` |
| Tunnel URL отдаёт `502 Bad Gateway` | Целевой сервис не отвечает на внутреннем порту | Проверить `docker compose ps` — статус целевого сервиса (`mcp-features`, `logs-server`) |
| n8n показывает `connection refused` или `domain not found` | URL устарел после рестарта tunnel | Перечитать новый URL из `docker compose logs <tunnel-service>` и обновить ноду |
| n8n MCP Client возвращает `401 Unauthorized` | Bearer Token credential в n8n не совпадает с `MCP_BEARER_TOKEN` в `.env` | Сравнить значения; либо очистить оба до пустых (auth off), либо синхронизировать |
| `tunnel --url` команда падает с `read tcp: connection refused` | Цепочка `depends_on` не дождалась здоровья целевого сервиса | Добавить healthcheck к целевому сервису + `condition: service_healthy` в depends_on |

---

## Apply на M5

Если у вас n8n в облаке (n8n.cloud / удалённый self-host), этот сетап подключается к домашке M5 без изменений основного workflow:

- **WF1** — нужен только MCP tunnel (нод `MCP Client` под капотом AI Agent).
- **WF2** — нужны оба tunnel (`GET Logs` для logs.json + MCP tunnel для трёх MCP-нод).

В сдаче M5 в README укажите, что использовали Cloudflare tunnel (или альтернативу) — это валидный production-pattern, не костыль. Если используете локальный n8n self-host на той же машине — туннель не нужен, ходите напрямую на `http://localhost:7777/mcp` / `http://host.docker.internal:7777/mcp`.

---

*Этот гайд — справочник. Он не часть обязательных требований M5, но если архитектура вашего проекта совпадает с описанным сценарием — это самый быстрый путь до рабочего стенда.*
