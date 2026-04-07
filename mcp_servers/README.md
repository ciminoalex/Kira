# MCP Servers — Kira

## Server attivi

### Gmail MCP
- **Pacchetto**: `@anthropic/gmail-mcp-server`
- **Trasporto**: stdio
- **Configurazione**: OAuth2 (client ID, secret, refresh token)

### Google Calendar MCP
- **Pacchetto**: `@anthropic/google-calendar-mcp-server`
- **Trasporto**: stdio
- **Configurazione**: OAuth2 (stesse credenziali Gmail)

### Microsoft 365 MCP (Fase 2)
- **Pacchetto**: `@softeria/ms-365-mcp-server`
- **Trasporto**: stdio
- **Configurazione**: Azure AD App Registration (client ID, tenant ID)
- **Preset**: email, calendar, contacts

### Supermemory MCP
- **URL**: `https://mcp.supermemory.ai/mcp`
- **Trasporto**: streamable-http
- **Autenticazione**: Bearer token (API key)

### Tavily MCP (Web Search)
- **Pacchetto**: `@tavily/mcp-server`
- **Trasporto**: stdio
- **Configurazione**: API key

### Filesystem MCP (Fase 4, opzionale)
- **Pacchetto**: `@anthropic/mcp-filesystem-server`
- **Trasporto**: HTTP via Tailscale
- **Configurazione**: Vedi `filesystem/config.json`
- **Prerequisiti**: PC fisso online con Tailscale

## Note
- Tutti i server stdio vengono avviati automaticamente dall'agente
- I server HTTP (Supermemory, Filesystem) richiedono che il servizio remoto sia raggiungibile
- Il filesystem MCP è opzionale: se il PC è offline, Kira prosegue senza di esso
