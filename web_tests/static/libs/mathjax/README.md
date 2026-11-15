MathJax 4.0.0
=============

`tex-mml-chtml.js` requires `sre/speech-worker.js` and `sre/mathmaps/`
for its default accessibility features. Keep these files together: a missing
speech worker can leave the startup promise pending and prevent responsive
display layout from running.

The SRE files and LICENSE come from the official, pinned npm distribution:
https://registry.npmjs.org/mathjax/-/mathjax-4.0.0.tgz

Test full pages with accessibility enabled, as well as isolated render fixtures.
