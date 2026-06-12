(async () => {
  const api = async (path, opts = {}) => {
    const r = await fetch('https://claude.ai/api' + path, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      ...opts,
    });
    const text = await r.text();
    return { ok: r.ok, data: text ? JSON.parse(text) : null };
  };

  const { data: orgs } = await api('/organizations');

  for (const org of orgs) {
    const convos = [];
    for (let offset = 0; ; offset += 100) {
      const { data } = await api(`/organizations/${org.uuid}/chat_conversations?limit=100&offset=${offset}`);
      const items = Array.isArray(data) ? data : data?.data ?? [];
      convos.push(...items);
      if (items.length < 100) break;
    }
    if (!convos.length) continue;

    if (!confirm(`"${org.name}": delete ${convos.length} conversations permanently?`)) continue;

    const bulk = await api(`/organizations/${org.uuid}/chat_conversations/delete_many`, {
      method: 'POST',
      body: JSON.stringify({ conversation_uuids: convos.map(c => c.uuid) }),
    });

    if (!bulk.ok) {
      for (const c of convos) {
        await api(`/organizations/${org.uuid}/chat_conversations/${c.uuid}`, {
          method: 'DELETE',
          body: JSON.stringify(c.uuid),
        });
        await new Promise(r => setTimeout(r, 250));
      }
    }
    console.log(`"${org.name}": done (${convos.length})`);
  }
  console.log('Finished — reload the page.');
})();
