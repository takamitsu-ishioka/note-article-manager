#!/usr/bin/env node
/* Render one TeX formula as a self-contained SVG using project-local MathJax. */
const fs = require("fs");
const {mathjax} = require("mathjax-full/js/mathjax.js");
const {TeX} = require("mathjax-full/js/input/tex.js");
const {SVG} = require("mathjax-full/js/output/svg.js");
const {liteAdaptor} = require("mathjax-full/js/adaptors/liteAdaptor.js");
const {RegisterHTMLHandler} = require("mathjax-full/js/handlers/html.js");
const {AllPackages} = require("mathjax-full/js/input/tex/AllPackages.js");

if (process.argv.length !== 4) {
  console.error("usage: render_tex_formula.js <input.tex> <output.svg>");
  process.exit(2);
}

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const tex = new TeX({packages: AllPackages});
const svg = new SVG({fontCache: "none"});
const document = mathjax.document("", {InputJax: tex, OutputJax: svg});
const source = fs.readFileSync(process.argv[2], "utf8");
const node = document.convert(source, {display: true});
const rendered = adaptor.outerHTML(node);
const match = rendered.match(/<svg[\s\S]*<\/svg>/);
if (!match) {
  throw new Error("MathJax did not produce an SVG element");
}
// ImageMagick does not resolve SVG currentColor consistently. Embed a stable
// foreground color and omit MathJax's HTML-only container wrapper.
fs.writeFileSync(process.argv[3], match[0].replaceAll("currentColor", "#111827"));
