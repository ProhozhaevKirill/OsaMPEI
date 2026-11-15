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
        // Leave room for italic text ink and font-metric rounding after enrichment.
        linebreaks: { inline: true, width: '95%', lineleading: 0.3 }
    }
};
