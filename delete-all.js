(async () => {
  const BULK_DELETE_SIZE = 100;
  const SINGLE_DELETE_CONCURRENCY = 8;
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

  const singleDelete = async (org, convo) => {
    const first = await api(`/organizations/${org.uuid}/chat_conversations/${convo.uuid}`, {
      method: 'DELETE',
      body: JSON.stringify(convo.uuid),
    });
    if (first.ok) return true;

    await new Promise(r => setTimeout(r, 1000));

    const second = await api(`/organizations/${org.uuid}/chat_conversations/${convo.uuid}`, {
      method: 'DELETE',
      body: JSON.stringify(convo.uuid),
    });
    return second.ok;
  };

  const deleteOneByOne = async (org, convos) => {
    let cursor = 0;
    let completed = 0;
    let deleted = 0;
    let failed = 0;

    const worker = async () => {
      for (;;) {
        const index = cursor;
        cursor += 1;
        if (index >= convos.length) return;

        const ok = await singleDelete(org, convos[index]);
        completed += 1;
        if (ok) {
          deleted += 1;
        } else {
          failed += 1;
        }

        if (completed % 10 === 0 || completed === convos.length) {
          log(`"${org.name}": processed ${completed}/${convos.length} conversations (${deleted} deleted${failed ? `, ${failed} failed` : ''})...`);
        }
      }
    };

    await Promise.all(
      Array.from({ length: Math.min(SINGLE_DELETE_CONCURRENCY, convos.length) }, worker),
    );

    return { deleted, failed };
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

    let deleted = 0;
    let failed = 0;

    for (let i = 0; i < convos.length; i += BULK_DELETE_SIZE) {
      const batch = convos.slice(i, i + BULK_DELETE_SIZE);
      log(`"${org.name}": bulk deleting ${i + 1}-${i + batch.length}/${convos.length}...`);

      const bulk = await api(`/organizations/${org.uuid}/chat_conversations/delete_many`, {
        method: 'POST',
        body: JSON.stringify({ conversation_uuids: batch.map(c => c.uuid) }),
      });

      if (bulk.ok) {
        deleted += batch.length;
        log(`"${org.name}": deleted ${deleted}/${convos.length} conversations...`);
      } else {
        log(`"${org.name}": bulk batch failed (${bulk.status}), deleting this batch with ${SINGLE_DELETE_CONCURRENCY} parallel requests...`);
        const result = await deleteOneByOne(org, batch);
        deleted += result.deleted;
        failed += result.failed;
      }
    }
    log(`"${org.name}": done (${deleted}/${convos.length}${failed ? `, ${failed} failed` : ''}).`);
  }
  log('Finished - reload the page.');
})();
