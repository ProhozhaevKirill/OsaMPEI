// Responsive read-only mathematics. Re-typeset original TeX, never split source strings.
(() => {
    // Cyrillic prose typed in math mode is a sequence of separate identifiers.
    // Keep each word atomic; preserve text commands and the stored source.
    const prepareSource = source => {
        let result = '', textMode = false;
        const scopes = [];
        for (let i = 0; i < source.length;) {
            const command = source.slice(i).match(/^\\(?:text[a-zA-Z]*|mbox|operatorname)\*?\s*\{/);
            if (command) {
                result += command[0]; i += command[0].length;
                scopes.push(textMode); textMode = true; continue;
            }
            const escaped = source.slice(i).match(/^\\(?:[a-zA-Z]+|[\s\S])/);
            if (escaped) { result += escaped[0]; i += escaped[0].length; continue; }
            if (source[i] === '%') {
                const end = source.indexOf('\n', i);
                if (end < 0) return result + source.slice(i);
                result += source.slice(i, end + 1); i = end + 1; continue;
            }
            if (source[i] === '{') scopes.push(textMode);
            if (source[i] === '}') textMode = scopes.pop() ?? false;
            const word = !textMode && source.slice(i).match(/^[\p{Script=Cyrillic}\p{M}]+/u);
            if (word) {
                // A text token survives semantic enrichment as one word.
                // TeXAtom/mathord groups can be flattened by that processing.
                result += '\\textit{' + word[0] + '}'; i += word[0].length;
            } else { result += source[i++]; }
        }
        return result;
    };
    const start = async () => {
        if (!window.MathJax?.startup) return;
        await MathJax.startup.promise;
        const entries = new Set();
        const dirty = new Set();
        let timer;
        let pending = Promise.resolve();
        const fit = entry => {
            const math = entry.host.querySelector('mjx-math');
            entry.host.classList.toggle('math-view-unbreakable', Boolean(math &&
                math.getBoundingClientRect().width > entry.host.clientWidth + 1));
        };
        const flush = () => {
            const changed = [...dirty].filter(entry => entry.host.isConnected && entry.host.clientWidth > 0);
            dirty.clear();
            pending = pending.then(async () => {
                if (!changed.length) return;
                const hosts = changed.map(entry => entry.host);
                MathJax.typesetClear(hosts);
                for (const entry of changed) entry.host.textContent = '\\[ ' + prepareSource(entry.source) + ' \\]';
                await MathJax.typesetPromise(hosts);
                changed.forEach(fit);
            }).catch(error => console.error('Unable to reflow displayed mathematics:', error));
            return pending;
        };
        const schedule = () => {
            clearTimeout(timer);
            timer = setTimeout(flush, 80);
        };
        window.MathDisplayLayout.reflow = async () => {
            clearTimeout(timer);
            do { await flush(); } while (dirty.size);
        };
        const observer = new ResizeObserver(records => {
            for (const {target, contentRect} of records) {
                const entry = target.mathDisplayEntry;
                if (Math.abs(entry.width - contentRect.width) <= 1) continue;
                entry.width = contentRect.width;
                dirty.add(entry);
            }
            if (dirty.size) schedule();
        });
        const discover = () => {
            let added = false;
            for (const item of MathJax.startup.document.math) {
                const output = item.typesetRoot;
                if (!item.display || !output?.isConnected || output.closest('.math-view, math-field')) continue;
                const host = document.createElement('span');
                host.className = 'math-view';
                output.before(host);
                host.appendChild(output);
                const entry = {host, source: item.math, width: host.getBoundingClientRect().width};
                host.mathDisplayEntry = entry;
                entries.add(entry);
                observer.observe(host);
                dirty.add(entry);
                added = true;
            }
            for (const entry of entries) {
                if (!entry.host.isConnected) { observer.unobserve(entry.host); entries.delete(entry); }
            }
            return added;
        };
        discover();
        await flush();
        // Also cover formula previews or answers inserted and typeset after load.
        new MutationObserver(() => { if (discover()) schedule(); })
            .observe(document.body, {childList: true, subtree: true});
    };
    window.MathDisplayLayout = {prepareSource, ready: document.readyState === 'complete' ? start() :
        new Promise((resolve, reject) => window.addEventListener('load', () => start().then(resolve, reject), {once: true}))};
})();
