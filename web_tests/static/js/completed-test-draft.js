// Consume the server's acknowledgement only after a successful save.
(() => {
    const entry = document.cookie.split('; ').find(item => item.startsWith('completed_test_draft='));
    if (!entry) return;
    const key = decodeURIComponent(entry.slice(entry.indexOf('=') + 1));
    try {
        if (key.startsWith('wt_draft_')) localStorage.removeItem(key);
    } catch (_) { return; }
    document.cookie = 'completed_test_draft=; Max-Age=0; Path=/; SameSite=Lax';
})();
