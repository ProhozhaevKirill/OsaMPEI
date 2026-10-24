// Reflow conditions from their original LaTeX when their available width changes.
window.addEventListener('load', async () => {
    if (!window.MathJax?.startup) return;
    await MathJax.startup.promise;
    const conditions = [...document.querySelectorAll('.express[data-expr]')];
    // A matrix cannot be split between lines. Fit only remaining indivisible math.
    const fitConditions = () => {
        for (const condition of conditions) {
            const container = condition.querySelector('mjx-container');
            const math = container?.querySelector('mjx-math');
            if (!math) continue;
            math.style.zoom = '';
            const width = math.getBoundingClientRect().width;
            if (width > container.clientWidth && container.clientWidth > 0) {
                math.style.zoom = (container.clientWidth - 1) / width;
            }
        }
    };
    fitConditions();
    const widths = new WeakMap();
    let timer;
    let pending = Promise.resolve();
    const observer = new ResizeObserver(entries => {
        const changed = [];
        for (const {target, contentRect} of entries) {
            const previous = widths.get(target);
            widths.set(target, contentRect.width);
            if (previous !== undefined && Math.abs(previous - contentRect.width) > 1) changed.push(target);
        }
        if (!changed.length) return;
        clearTimeout(timer);
        timer = setTimeout(() => {
            pending = pending.then(async () => {
                MathJax.typesetClear(conditions);
                for (const condition of conditions) {
                    condition.textContent = '\\[ ' + condition.dataset.expr + ' \\]';
                }
                await MathJax.typesetPromise(conditions);
                fitConditions();
            }).catch(error => console.error('Не удалось обновить перенос условий:', error));
        }, 100);
    });
    conditions.forEach(condition => observer.observe(condition));
});
