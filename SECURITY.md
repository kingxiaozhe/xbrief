# Security policy

## Credential handling

XBrief needs a locally configured authentication context for its external X client. Never commit credentials, cookie files, exported browser data, personal Vault contents, fetched discussions, or generated reports.

The CLI accepts no arbitrary backend tool name. Its adapter permits only get_tweet and get_tweet_replies, validates the configured credential file before use, rejects symlinks and unsafe permissions, and redacts authentication-like values from backend errors.

## Reporting a vulnerability

Please open a private GitHub security advisory for credential exposure, unsafe file handling, arbitrary command execution, unsafe backend access, or data-loss risks. Do not include live credentials in the report.
