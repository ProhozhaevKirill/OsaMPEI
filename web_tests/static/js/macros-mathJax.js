window.MathJax = {
    tex: {
        macros: {
            differentialD: "{\\,\\mathrm{d}}",
            infin: "\\, \\mathrm{\\infty}",
            tg: "\\mathrm{tan}",
            th: "\\mathrm{tanh}",
            ch: "\\mathrm{cosh}",
        }
    },
    output: {
        displayAlign: 'center',
        displayOverflow: 'linebreak',
        // A small width reserve avoids overflow from font-metric rounding.
        linebreaks: { inline: true, width: '98%', lineleading: 0.3 }
    }
};
