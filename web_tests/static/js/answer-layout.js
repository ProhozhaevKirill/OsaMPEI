// Soft-wrap every MathLive field without changing its stored LaTeX.
// Explicit Enter breaks use native MathLive editing and remain in the saved value.
// Persist empty editors as empty strings rather than layout-only LaTeX rows.
window.MathFieldLayout = {
    normalizeValue(value) {
        const latex = String(value || '');
        return latex.replace(/\\displaylines|\\text(?=\{)|\\\\|[{}\s]/g, '') ? latex : '';
    },
    read(field) { return this.normalizeValue(field?.value); },
};

document.addEventListener('DOMContentLoaded', async () => {
    await customElements.whenDefined('math-field');
    const selector = 'math-field';
    const updates = new WeakMap();
    const initialize = field => {
        if (!field.shadowRoot || field.shadowRoot.getElementById('answer-wrap-style')) return;
        // Empty presentation wrappers and line breaks are not typed symbols.
        const hasContent = () => Boolean(window.MathFieldLayout.read(field)) ||
            [...field.shadowRoot.querySelectorAll('.ML__raw-latex')].some(node => node.textContent.length > 0);
        let normalizingEmpty = false;
        const normalizeRestoredEmpty = () => {
            if (normalizingEmpty || field.mode === 'latex' || hasContent()) return;
            field.scrollTop = 0;
            field.scrollLeft = 0;
            const content = field.shadowRoot.querySelector('.ML__content');
            if (content) { content.scrollTop = 0; content.scrollLeft = 0; }
            if (!field.value.startsWith('\\displaylines{') || field.value === '\\displaylines{}') return;
            normalizingEmpty = true;
            try {
                field.insert('\\displaylines{}', {insertionMode: 'replaceAll', format: 'latex', mode: 'math'});
                field.position = 0;
            } finally { normalizingEmpty = false; }
        };
        let initialPointer = false;
        const clearEntireMultiline = event => {
            const ranges = field.selection.ranges;
            if (field.readOnly || !field.value.startsWith('\\displaylines{') ||
                field.lastOffset === 0 || ranges.length !== 1 ||
                ranges[0][0] !== 0 || ranges[0][1] !== field.lastOffset) return false;
            // Replace the whole root in one undoable edit. Native deletion only
            // clears its cells, leaving all old empty rows and their height.
            event.preventDefault();
            event.stopImmediatePropagation();
            field.insert('\\displaylines{}', {insertionMode: 'replaceAll', format: 'latex', mode: 'math'});
            field.position = 0;
            return true;
        };
        field.addEventListener('beforeinput', event => {
            if (event.inputType?.startsWith('delete')) clearEntireMultiline(event);
        });
        let pendingRawDeletion = false;
        let rawRecoveryQueued = false;
        field.addEventListener('keydown', event => {
            if (field.readOnly || field.mode === 'latex' || event.isComposing ||
                event.ctrlKey || event.altKey || event.metaKey) return;
            const russianPeriod = event.code === 'Slash' && event.key === '.';
            const russianLetter = event.code === 'Quote' && /^[эЭ]$/.test(event.key);
            if (!russianPeriod && !russianLetter) return;
            // MathLive binds these physical keys to fractions and mode changes.
            event.preventDefault();
            event.stopImmediatePropagation();
            field.insert(event.key, {format: 'latex', mode: field.mode});
        }, {capture: true});
        field.addEventListener('keydown', event => {
            if (['Backspace', 'Delete'].includes(event.key)) {
                if (clearEntireMultiline(event)) return;
                pendingRawDeletion = field.mode === 'latex';
            } else if (event.key.length === 1 || ['Enter', 'Escape'].includes(event.key)) {
                pendingRawDeletion = false;
            }
        }, {capture: true});

        // This prompt is outside MathLive's rendered content. Its visibility
        // depends only on content, never focus, clicks or render timing.
        const prompt = document.createElement('span');
        prompt.id = 'mathfield-prompt';
        prompt.setAttribute('aria-hidden', 'true');
        const padding = getComputedStyle(field);
        prompt.style.top = `calc(${padding.paddingTop} + 6px)`;
        prompt.style.left = `calc(${padding.paddingLeft} + 5px)`;
        const updatePrompt = () => {
            const text = field.getAttribute('placeholder') || '';
            if (prompt.textContent !== text) prompt.textContent = text;
            const hidden = hasContent() || !prompt.textContent;
            if (prompt.hidden !== hidden) prompt.hidden = hidden;
        };
        field.shadowRoot.appendChild(prompt);
        updatePrompt();
        field.addEventListener('input', updatePrompt);
        const startAtBeginning = () => {
            normalizeRestoredEmpty();
            updatePrompt();
            field.focus();
            field.position = 0;
        };
        const isToolbar = event => event.composedPath().some(node =>
            node instanceof Element && node.matches('[role="button"], button'));
        const beginInitialGesture = event => {
            if (isToolbar(event) || field.readOnly ||
                (event.button !== undefined && event.button !== 0) ||
                hasContent()) return;
            event.preventDefault();
            event.stopImmediatePropagation();
            initialPointer = true;
            startAtBeginning();
        };
        const finishInitialGesture = event => {
            if (hasContent()) { initialPointer = false; return; }
            if (!initialPointer || isToolbar(event)) return;
            event.preventDefault();
            event.stopImmediatePropagation();
            startAtBeginning();
            if (event.type === 'click') initialPointer = false;
        };
        // Browsers can synthesize mouse events after pointer/touch events.
        // Consume the entire first gesture, not just pointerdown or focus.
        for (const type of ['pointerdown', 'mousedown', 'touchstart']) {
            field.addEventListener(type, beginInitialGesture, {capture: true, passive: false});
        }
        for (const type of ['pointerup', 'mouseup', 'touchend', 'click']) {
            field.addEventListener(type, finishInitialGesture, {capture: true, passive: false});
        }
        field.addEventListener('pointercancel', () => { initialPointer = false; }, {capture: true});
        field.addEventListener('focus', () => {
            if (!field.readOnly && !hasContent()) {
                normalizeRestoredEmpty();
                field.position = 0;
            }
        });
        // MathLive's native vertical arrows follow formula structure, so they
        // cannot see CSS soft wraps. At root level follow the rendered rows;
        // inside fractions, powers and matrices retain structural navigation.
        let verticalX = null;
        let verticalAnchor = null;
        const resetVertical = () => { verticalX = null; verticalAnchor = null; };
        field.addEventListener('pointerdown', resetVertical, {capture: true});
        field.addEventListener('input', resetVertical);
        field.addEventListener('keydown', event => {
            if (!['ArrowUp', 'ArrowDown'].includes(event.key)) {
                resetVertical();
                return;
            }
            if (event.ctrlKey || event.altKey || event.metaKey || field.readOnly || field.mode === 'latex' ||
                field.classList.contains('matrix-answer') ||
                Number(field.closest('.answer-row')?.querySelector('.type-field')?.selectedOptions[0]?.dataset.typeCode) === 4 ||
                field.getElementInfo(field.position)?.depth > 0) return;
            const caret = field.shadowRoot.querySelector('.ML__caret, .ML__text-caret');
            if (!caret) return;
            const rect = caret.getBoundingClientRect();
            const rows = [];
            for (let offset = 1; offset <= field.lastOffset; offset++) {
                const info = field.getElementInfo(offset);
                const bounds = info?.bounds;
                if (info?.depth !== 0 || !bounds?.width || !bounds.height) continue;
                // Scripts and fractions can start higher than their neighbors
                // on the same visual line. Group by overlapping vertical spans.
                let row = rows.at(-1);
                if (!row || Math.min(row.bottom, bounds.bottom) <= Math.max(row.top, bounds.top)) {
                    row = {top: bounds.top, bottom: bounds.bottom, stops: []};
                    rows.push(row);
                }
                row.top = Math.min(row.top, bounds.top);
                row.bottom = Math.max(row.bottom, bounds.bottom);
                row.stops.push({offset, x: bounds.right});
            }
            const currentRow = rows.find(row => row.stops.some(stop => stop.offset === field.position)) ||
                rows.find(row => rect.top < row.bottom && rect.bottom > row.top);
            if (!currentRow || rows.length < 2) return;
            const direction = event.key === 'ArrowUp' ? -1 : 1;
            const target = rows[rows.indexOf(currentRow) + direction];
            event.preventDefault();
            event.stopImmediatePropagation();
            if (!target) return;
            verticalX ??= rect.left;
            const offset = target.stops.reduce((best, stop) =>
                Math.abs(stop.x - verticalX) < Math.abs(best.x - verticalX) ? stop : best).offset;
            if (event.shiftKey) {
                verticalAnchor ??= field.position;
                field.selection = {ranges: [[Math.min(verticalAnchor, offset), Math.max(verticalAnchor, offset)]],
                    direction: offset < verticalAnchor ? 'backward' : 'forward'};
            } else {
                verticalAnchor = null;
                field.position = offset;
            }
        }, {capture: true});
        // Keep initial/empty layout aligned at the top too. Wrapping styles are
        // disabled on empty fields and matrix answers, so this stays separate.
        const alignment = document.createElement('style');
        alignment.textContent = `
            .ML__container { vertical-align: top !important; align-items: flex-start !important; }
            .ML__content { align-self: flex-start !important; text-align: left; }
            :host { position: relative !important; }
            .ML__content-placeholder { display: none !important; }
            #mathfield-prompt {
                position: absolute;
                z-index: 1;
                pointer-events: none;
                color: var(--placeholder-color, #929292);
                font: inherit;
                line-height: 1.5;
                white-space: pre-wrap;
                max-width: calc(100% - 100px);
            }
            #mathfield-prompt[hidden] { display: none !important; }
        `;
        field.shadowRoot.appendChild(alignment);
        // Keep native undo, selection and matrix row editing. Never replace .value
        // while typing: doing so loses the caret and can discard existing rows.
        field.keybindings = [
            {key: '[Enter]', ifMode: 'math', command: 'addRowAfter'},
            {key: 'shift+[Enter]', ifMode: 'math', command: 'addRowAfter'},
            ...field.keybindings,
        ];
        // Native addRowAfter resets text input to math mode. Keep prose as
        // prose on the new line, including when Enter comes from the sink.
        field.addEventListener('keydown', event => {
            if (event.key !== 'Enter' || event.isComposing || event.ctrlKey ||
                event.metaKey || event.altKey || field.readOnly || field.mode !== 'text') return;
            event.preventDefault();
            event.stopPropagation();
            field.executeCommand('addRowAfter');
            field.executeCommand(['switchMode', 'text']);
        }, {capture: true});
        const style = document.createElement('style');
        style.id = 'answer-wrap-style';
        style.textContent = `
            :host {
                height: auto !important;
                max-height: none !important;
                min-width: 0;
            }
            /* Keep the root caret's zero-width anchor inline at the baseline;
               overlay only its stroke so navigation cannot change wrapping.
               Nested carets retain MathLive's native script/fraction metrics. */
            .ML__content > .ML__latex > .ML__base > :is(.ML__caret, .ML__text-caret),
            .ML__content > .ML__latex > .ML__mtable > .col-align-l > .ML__vlist-t > .ML__vlist-r > .ML__vlist > span > span > :is(.ML__caret, .ML__text-caret) {
                display: inline !important;
                position: relative !important;
                width: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                border: 0 !important;
            }
            .ML__content > .ML__latex > .ML__base > :is(.ML__caret, .ML__text-caret)::after,
            .ML__content > .ML__latex > .ML__mtable > .col-align-l > .ML__vlist-t > .ML__vlist-r > .ML__vlist > span > span > :is(.ML__caret, .ML__text-caret)::after {
                position: absolute !important;
            }
            .ML__container {
                max-width: 100%;
                box-sizing: border-box;
            }
            .ML__content {
                display: block !important;
                min-width: 0;
                overflow: auto;
            }
            .ML__content > .ML__latex {
                display: block !important;
                width: 100% !important;
                min-width: 0;
                white-space: normal !important;
                overflow-wrap: anywhere;
            }
            .ML__content > .ML__latex > .ML__base {
                display: inline !important;
                width: auto !important;
                white-space: normal !important;
                overflow-wrap: anywhere;
            }
            .ML__content > .ML__latex > .ML__base > .ML__text {
                white-space: break-spaces;
                overflow-wrap: anywhere;
            }
            /* MathLive renders its root multiline environment as positioned rows.
               Give only those rows normal flow so each explicit line can wrap
               and grow independently. Fractions and matrices stay atomic. */
            .ML__latex > .ML__mtable {
                display: block;
                width: 100%;
            }
            .ML__latex > .ML__mtable > .col-align-l,
            .ML__latex > .ML__mtable > .col-align-l > .ML__vlist-t,
            .ML__latex > .ML__mtable > .col-align-l > .ML__vlist-t > .ML__vlist-r,
            .ML__latex > .ML__mtable > .col-align-l > .ML__vlist-t > .ML__vlist-r > .ML__vlist {
                display: block;
                height: auto !important;
                width: 100%;
            }
            .ML__latex > .ML__mtable > .col-align-l > .ML__vlist-t > .ML__vlist-r > .ML__vlist > span {
                display: block;
                position: static;
                height: auto;
            }
            .ML__latex > .ML__mtable > .col-align-l > .ML__vlist-t > .ML__vlist-r > .ML__vlist > span > span:not(.ML__pstrut) {
                display: block !important;
                height: auto !important;
                min-height: 1.5em;
                white-space: normal;
                overflow-wrap: anywhere;
            }
            .ML__latex > .ML__mtable > .col-align-l > .ML__vlist-t > .ML__vlist-r > .ML__vlist > span > span > .ML__text {
                white-space: break-spaces;
                overflow-wrap: anywhere;
            }
            .ML__latex:has(> .ML__mtable) > .ML__strut,
            .ML__latex:has(> .ML__mtable) > .ML__strut--bottom,
            .ML__latex > .ML__mtable > .col-align-l > .ML__vlist-t > .ML__vlist-r > .ML__vlist-s,
            .ML__latex > .ML__mtable > .col-align-l > .ML__vlist-t > .ML__vlist-r > .ML__vlist > span > .ML__pstrut {
                display: none;
            }
        `;
        // Empty fields retain MathLive's native single-line layout from the start.
        // Applying wrapping to its temporary empty/placeholder markup causes a
        // different size before the first focus-triggered render.
        const updateLayout = () => {
            // Draft restoration assigns .value without input events. Repair old
            // empty roots when inactive, while leaving actively entered newlines.
            if (!field.hasFocus()) normalizeRestoredEmpty();
            // MathLive leaves an empty raw-command group after the final slash
            // is deleted. Exit via its public command API so Backspace/arrows
            // edit the surrounding expression again, preserving undo.
            if (pendingRawDeletion && !rawRecoveryQueued) {
                rawRecoveryQueued = true;
                // Read the final rendered command, not intermediate markup from
                // a rapid sequence of typing/deletion events in the same frame.
                requestAnimationFrame(() => requestAnimationFrame(() => {
                    rawRecoveryQueued = false;
                    if (pendingRawDeletion && field.mode === 'latex' &&
                        field.shadowRoot.querySelector('.ML__latex-caret') &&
                        ![...field.shadowRoot.querySelectorAll('.ML__raw-latex')].some(node => node.textContent)) {
                        pendingRawDeletion = false;
                        field.executeCommand(['switchMode', 'math']);
                    }
                }));
            }
            if (field.mode !== 'latex') pendingRawDeletion = false;
            updatePrompt();
            const type = field.closest('.answer-row')?.querySelector('.type-field');
            const matrix = field.classList.contains('matrix-answer') || Number(type?.selectedOptions[0]?.dataset.typeCode) === 4;
            const disabled = !field.value || matrix;
            if (style.disabled !== disabled) style.disabled = disabled;
        };
        style.disabled = !field.value;
        field.shadowRoot.appendChild(style);
        updates.set(field, updateLayout);
        updateLayout();
        field.addEventListener('input', updateLayout);
        field.addEventListener('change', updateLayout);
        // Restoring a saved answer sets .value without an input event.
        const observer = new MutationObserver(updateLayout);
        observer.observe(field.shadowRoot, {childList: true, subtree: true, characterData: true});
        field.setAttribute('aria-multiline', 'true');
        field.shadowRoot.querySelector('[part="keyboard-sink"]')?.setAttribute('aria-multiline', 'true');
    };
    const initializeWithin = root => {
        if (root.matches?.(selector)) initialize(root);
        root.querySelectorAll(selector).forEach(initialize);
    };
    initializeWithin(document);
    // The teacher's editor adds answer rows and task variants without reloading.
    new MutationObserver(records => {
        for (const record of records) {
            for (const node of record.addedNodes) {
                if (node.nodeType === Node.ELEMENT_NODE) initializeWithin(node);
            }
        }
    }).observe(document.body, {childList: true, subtree: true});
    document.addEventListener('change', event => {
        if (!event.target.matches('.type-field')) return;
        const field = event.target.closest('.answer-row')?.querySelector('math-field.answer-field');
        if (field) updates.get(field)?.();
    });
});
