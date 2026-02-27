# Pet: Continue Conversation

Continues a previous conversation in a new session.

## Description

Loads the context from a previous conversation and prepares the pet for continuing that conversation. This is useful when you want to resume work on a task after a break.

## Usage

```
/pet:continue [conversation_id]
```

If no conversation ID is provided, lists conversations that can be continued.

## Options

- `conversation_id` - Optional ID of the conversation to continue
- `mode` - Continuation mode: `context` (default) or `full`
- `new_message` - Optional new message to start with

## Examples

List continuable conversations:
```
/pet:continue
```

Continue a specific conversation:
```
/pet:continue abc123def456
```

Continue with a new message:
```
/pet:continue abc123def456 --new_message="Let's add more features"
```

## Continuation Modes

### Context Mode (default)
Provides a summary of the previous conversation with key points and the last exchange. Best for quick reference.

### Full Mode
Includes the full message history. Use this when you need complete context.

## Behavior

When you continue a conversation:

1. The pet loads the conversation context
2. Context is formatted for the new session
3. Context is copied to clipboard for easy pasting
4. Pet shows a "continue" mood to indicate active session

## Notes

- The conversation history is preserved - this starts a new session with context
- Use `/pet:status` to see current conversation info
- The pet will remember files from the previous conversation
- Tags from the previous conversation are carried over
