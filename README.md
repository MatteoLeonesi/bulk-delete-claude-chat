# bulk-delete-claude-chat

Delete **all** your claude.ai conversations at once, i created it because the "Select all" button on `/recents` only covers the rows rendered on screen. This script calls the internal API instead, so it gets everything.

> ⚠️ Deletion is permanent. Unofficial API, may break anytime.

## How to
- Open [claude.ai](https://claude.ai), press `F12` → **Console**
- Paste the contents of [`delete-all.js`](delete-all.js), hit Enter
- Confirm the dialog (one per organization)
- Wait for `Finished` in the console, then reload the page
- ⚠️ Be patient: conversations disappear from the UI **slowly, over several minutes/hours**; that's normal
