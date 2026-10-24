// Wrap the top-level answer visually; never insert line breaks into its LaTeX.
document.addEventListener('DOMContentLoaded', async () => {
    await customElements.whenDefined('math-field');
    for (const field of document.querySelectorAll('math-field.answer:not(.matrix-answer)')) {
        if (!field.shadowRoot || field.shadowRoot.getElementById('answer-wrap-style')) continue;
        const style = document.createElement('style');
        style.id = 'answer-wrap-style';
        style.textContent = `
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
        `;
        // Empty answers retain MathLive's native single-line layout from the start.
        // Applying wrapping to its temporary empty/placeholder markup causes a
        // different size before the first focus-triggered render.
        const updateLayout = () => {
            const disabled = !field.value;
            if (style.disabled !== disabled) style.disabled = disabled;
        };
        style.disabled = !field.value;
        field.shadowRoot.appendChild(style);
        updateLayout();
        field.addEventListener('input', updateLayout);
        field.addEventListener('change', updateLayout);
        // Restoring a saved answer sets .value without an input event.
        const observer = new MutationObserver(updateLayout);
        observer.observe(field.shadowRoot, {childList: true, subtree: true, characterData: true});
        field.setAttribute('aria-multiline', 'true');
        field.shadowRoot.querySelector('[part="keyboard-sink"]')?.setAttribute('aria-multiline', 'true');
    }
});
