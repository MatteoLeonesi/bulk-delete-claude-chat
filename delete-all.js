(async () => {
  const log = message => console.log(`[claude-bulk-delete] ${message}`);

  const api = async (path, opts = {}) => {
    const r = await fetch('https://claude.ai/api' + path, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      ...opts,
    });
    const text = await r.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }
    }
    return { ok: r.ok, status: r.status, data };
  };

  log('Loading organizations...');
  const { data: orgs } = await api('/organizations');
  log(`Found ${orgs.length} organization${orgs.length === 1 ? '' : 's'}.`);

  for (const org of orgs) {
    log(`"${org.name}": loading conversations...`);
    const convos = [];
    for (let offset = 0; ; offset += 100) {
      const { data } = await api(`/organizations/${org.uuid}/chat_conversations?limit=100&offset=${offset}`);
      const items = Array.isArray(data) ? data : data?.data ?? [];
      convos.push(...items);
      log(`"${org.name}": loaded ${convos.length} conversation${convos.length === 1 ? '' : 's'}...`);
      if (items.length < 100) break;
    }
    if (!convos.length) {
      log(`"${org.name}": no conversations found.`);
      continue;
    }

    if (!confirm(`"${org.name}": delete ${convos.length} conversations permanently?`)) continue;

    log(`"${org.name}": sending bulk delete request for ${convos.length} conversations...`);
    const bulk = await api(`/organizations/${org.uuid}/chat_conversations/delete_many`, {
      method: 'POST',
      body: JSON.stringify({ conversation_uuids: convos.map(c => c.uuid) }),
    });

    if (!bulk.ok) {
      log(`"${org.name}": bulk delete failed (${bulk.status}), deleting one by one...`);
      for (const [index, c] of convos.entries()) {
        await api(`/organizations/${org.uuid}/chat_conversations/${c.uuid}`, {
          method: 'DELETE',
          body: JSON.stringify(c.uuid),
        });
        if ((index + 1) % 10 === 0 || index + 1 === convos.length) {
          log(`"${org.name}": deleted ${index + 1}/${convos.length} conversations...`);
        }
        await new Promise(r => setTimeout(r, 250));
      }
    } else {
      log(`"${org.name}": bulk delete accepted.`);
    }
    log(`"${org.name}": done (${convos.length}).`);
  }
  log('Finished - reload the page.');
})();
