Delete **all** your claude.ai conversations at once, i created it because the "Select all" button on `/recents` only covers the rows rendered on screen. 

⚠️ These are internal Claude.ai web app endpoints, not public documented Anthropic APIs. They were inferred from browser network requests and may change or stop working at any time. Not affiliated with Anthropic. Use it only with your own Claude account.

### How to
- Open https://claude.ai/recents and press `F12` → **Console**
- Paste the contents of [`delete-all.js`](delete-all.js), hit Enter
- Confirm the dialog (one per organization)
- Be patient: conversations disappear from the UI **slowly, over several minutes**; that's normal
- Keep the claude.ai tab open until the console shows `Finished`; closing, refreshing, or navigating away from the page can stop the deletion process.

[![Show HN](https://img.shields.io/badge/Show%20HN-discussion-ff6600?logo=ycombinator&logoColor=white)](https://news.ycombinator.com/item?id=48505161)

### License
MIT. See [`LICENSE`](LICENSE).
