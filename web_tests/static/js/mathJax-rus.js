MathfieldElement.locale = 'ru';  // Устанавливаем русский язык

customElements.whenDefined('math-field').then(() => {
    console.log("Locale:", MathfieldElement.locale);
    console.log(MathfieldElement.strings[MathfieldElement.locale.substring(0, 2)]);
});

// Перехват пробела в math-field
$(document).on('keydown', 'math-field', function(e) {
    if (e.key === ' ') {
        e.preventDefault();
        this.insert("\\;");
    }
});

// Явный перенос строки по Enter
$('.container').on('keydown', 'math-field', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const mf = this;
        const content = mf.getValue();
        if (!content.startsWith('\\displaylines{')) {
            mf.setValue('\\displaylines{\n    ' + content + '\n    \\\\\n    \n}');
        } else {
            mf.insert('\\\\\n');
        }
        mf.executeCommand('moveToMathfieldEnd');
    }
});

// ─── Автоматический перенос при переполнении ───────────────────────────────

const _autoBreakTimers = new WeakMap();

$('.container').on('input', 'math-field', function() {
    const mf = this;
    if (_autoBreakTimers.has(mf)) clearTimeout(_autoBreakTimers.get(mf));
    _autoBreakTimers.set(mf, setTimeout(function() {
        requestAnimationFrame(function() { _tryAutoBreak(mf); });
    }, 350));
});

function _tryAutoBreak(mf) {
    if (!_isOverflowing(mf)) return;

    const latex = mf.getValue();
    if (!latex) return;

    const broken = _insertLineBreak(latex);
    if (broken === latex) return;

    mf.setValue(broken);
    mf.executeCommand('moveToMathfieldEnd');
}

/** Определяет, переполнено ли поле: DOM-измерение + эвристика */
function _isOverflowing(mf) {
    const containerW = mf.offsetWidth || mf.clientWidth;
    if (!containerW) return false;

    // DOM: проверяем ширину дочерних span/div (MathLive рендерит в них)
    const children = mf.querySelectorAll(':scope > span, :scope > div');
    for (const el of children) {
        if (el.scrollWidth > containerW + 5) return true;
    }
    // Запасной вариант: сам элемент
    if (mf.scrollWidth > containerW + 5) return true;

    // Эвристика: подсчёт примерной ширины LaTeX-строки
    return _estimateWidth(mf.getValue()) > containerW * 0.88;
}

/** Грубая оценка визуальной ширины LaTeX в пикселях */
function _estimateWidth(latex) {
    if (!latex) return 0;
    let w = 0, i = 0;
    while (i < latex.length) {
        if (latex[i] === '\\') {
            let j = i + 1;
            while (j < latex.length && /[a-zA-Z]/.test(latex[j])) j++;
            const cmd = latex.slice(i + 1, j);
            w += ['frac','sqrt','int','sum','prod','lim','infty'].includes(cmd) ? 38 : 18;
            i = j;
        } else if ('{}^_ '.includes(latex[i])) {
            i++;
        } else {
            w += 13; // обычный символ / цифра / оператор
            i++;
        }
    }
    return w;
}

/** Оборачивает в \displaylines и вставляет \\ в конце переполненной строки */
function _insertLineBreak(latex) {
    const DL = '\\displaylines{';
    let lines;

    if (latex.startsWith(DL) && latex.endsWith('}')) {
        const inner = latex.slice(DL.length, -1);
        lines = inner.split('\\\\').map(function(s) { return s.trim(); });
    } else {
        lines = [latex];
    }

    // Пытаемся разбить последнюю строку
    const last = lines[lines.length - 1];
    const brokenLast = _breakLine(last);
    if (brokenLast === last) return latex; // не нашли точку разрыва

    lines[lines.length - 1] = brokenLast;
    return DL + lines.join('\\\\\n') + '}';
}

/** Разбивает строку LaTeX по ближайшему оператору к середине */
function _breakLine(s) {
    const minPos  = Math.floor(s.length * 0.20); // не рвать слишком рано
    const midPos  = Math.floor(s.length * 0.55); // желательная точка

    let depth = 0;
    let best  = -1;

    for (let i = 0; i < s.length; i++) {
        const c = s[i];
        if      (c === '{') { depth++; continue; }
        else if (c === '}') { depth--; continue; }
        if (depth !== 0) continue;

        // Разрыв допускается после =, +, -, , и пробела
        if (i >= minPos && (c === '=' || c === '+' || c === '-' || c === ',' || c === ' ')) {
            best = i;
            if (i >= midPos) break; // дальше первой точки после середины не идём
        }
    }

    if (best === -1) return s; // нет подходящей точки

    const before = s.slice(0, best + 1).trimEnd();
    const after  = s.slice(best + 1).trimStart();
    if (!after) return s;

    return before + '\\\\\n' + after;
}
