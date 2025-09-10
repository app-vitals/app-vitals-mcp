# Trello MCP Server

MCP server for managing Trello cards with CRUD operations.

## Getting Trello Credentials

You need two things:
1. **API Key** - Your Trello API key
2. **Token** - An authorization token (NOT the API secret)

### Easy Setup with Script

Use the included script for guided setup:

```bash
python scripts/generate_trello_token.py
```

This script will:
- Auto-detect your API key or prompt for it
- Open your browser to the authorization page
- Guide you through token generation
- Optionally save credentials to `.env`

### Manual Setup

1. **Get your API Key:**
   - Go to https://trello.com/power-ups/admin
   - Create a new Power-Up (or use existing one)
   - Copy the API Key (not the secret!)

2. **Generate a Token:**
   - Visit: `https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&key=YOUR_API_KEY`
   - Replace `YOUR_API_KEY` with your actual API key from step 1
   - Click "Allow" to authorize
   - Copy the generated token

3. **Set environment variables:**
   ```bash
   export TRELLO_API_KEY="your_api_key_here"
   export TRELLO_TOKEN="your_generated_token_here"
   ```

   Or add to `.env` file:
   ```
   TRELLO_API_KEY=your_api_key_here
   TRELLO_TOKEN=your_generated_token_here
   ```

## Running the Server

```bash
mcp-server-trello
```

## Available Tools

- `trello_get_boards` - List all accessible boards
- `trello_get_lists` - Get lists in a board
- `trello_create_card` - Create a new card
- `trello_get_card` - Get card by ID
- `trello_list_cards` - List cards on a board or in a list
- `trello_update_card` - Update card properties
- `trello_delete_card` - Delete a card

## Testing

### Unit Tests
```bash
uv run pytest tests/servers/trello/test_client.py -v
uv run pytest tests/servers/trello/test_server.py -v
```

### Integration Tests
Requires valid credentials and an "Integration Testing" board with "To Do" and "Done" lists:

```bash
uv run pytest tests/servers/trello/test_integration.py -v -m integration
```

## Common Issues

- **401 Unauthorized**: The token is incorrect. Make sure you generated a token (not using the API secret)
- **Board not found**: Create an "Integration Testing" board in Trello for tests