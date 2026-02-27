# Pet: Restore Conversation Context

Restores context from a previous conversation for continuation.

## Description

Loads the context from a previous conversation and formats it for use in a new conversation. This helps maintain continuity when working on related tasks across multiple sessions.

## Usage

```
/pet:restore [conversation_id]
```

If no conversation ID is provided, lists recent conversations that can be restored.

## Options

- `conversation_id` - Optional ID of the conversation to restore
- `format` - Output format: `markdown` (default) or `json`
- `include_messages` - Include message history (default: true)

## Examples

List recent conversations:
```
/pet:restore
```

Restore a specific conversation:
```
/pet:restore abc123def456
```

Restore with minimal context:
```
/pet:restore abc123def456 --include_messages=false
```

## Output Format

The restored context includes:

1. **Conversation Header** - Title and date
2. **Summary** - What was discussed
3. **Key Points** - Main topics and outcomes
4. **Files Discussed** - Files that were touched
5. **Last Exchange** - The last user/assistant messages

## Notes

- The context is automatically copied to the clipboard
- Paste the context into a new conversation to continue
- Use `/pet:continue` to automatically switch to continuation mode
- Recent conversations are prioritized in the listing
