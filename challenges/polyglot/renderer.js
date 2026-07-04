/* renderer.js  —  This text is stored, byte for byte, inside the pixels of
   triptych.png. When the file is opened as HTML, a tiny bootstrap loads the
   file into an <img>, reads the pixels back off a <canvas>, reconstructs
   this source from them, and runs it. So the code you are reading rendered
   the page you are looking at, out of its own image data. The ouroboros:
   pixels -> code -> page.

   Contract from the bootstrap (see the <script> appended after IEND):
     window.__SRC__  = this source, as a string  (for the quine panel)
     window.__PX__   = { w, h, rgb }  the decoded pixel bytes (R,G,B stream)
     location.href   = the file itself, a valid PNG  (for the <img>)         */
(function () {
  var P = window.__PX__, SRC = window.__SRC__;

  document.documentElement.innerHTML =
    '<head><meta charset="utf-8"><title>triptych</title><style>' +
    '*{box-sizing:border-box}body{margin:0;font:14px/1.5 ui-monospace,Menlo,Consolas,monospace;' +
    'background:#0b0e14;color:#c8d0da}h1{font-size:18px;margin:0 0 4px;color:#8ab4f8}' +
    '.sub{color:#6b7684;margin:0 0 16px}.wrap{max-width:1000px;margin:0 auto;padding:24px}' +
    '.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}' +
    '.card{background:#12161f;border:1px solid #222a37;border-radius:10px;padding:12px;overflow:hidden}' +
    '.card h2{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#6b7684;margin:0 0 8px}' +
    'img,canvas{width:100%;image-rendering:pixelated;border-radius:6px;display:block}' +
    'pre{margin:0;max-height:340px;overflow:auto;white-space:pre-wrap;word-break:break-word;font-size:12px;color:#9fb2c8}' +
    '.tags{margin:14px 0 0;display:flex;gap:8px;flex-wrap:wrap}' +
    '.tag{font-size:12px;padding:4px 10px;border-radius:999px;background:#1b2331;border:1px solid #2a3444}' +
    '.tag b{color:#a6e3a1}@media(max-width:720px){.grid{grid-template-columns:1fr}}</style></head>' +
    '<body><div class=wrap>' +
    '<h1>triptych.png</h1>' +
    '<p class=sub>one file &mdash; a valid <b>PNG</b>, a valid <b>ZIP</b>, and this <b>HTML</b> page. ' +
    'this page was decoded from the PNG&rsquo;s own pixels.</p>' +
    '<div class=grid>' +
    '<div class=card><h2>the PNG, drawn as an image</h2><img src="' + location.href + '"></div>' +
    '<div class=card><h2>same pixels, re-rendered live &rarr;</h2><canvas id=cv></canvas></div>' +
    '</div>' +
    '<div class=tags>' +
    '<span class=tag>bytes decoded: <b>' + SRC.length + '</b></span>' +
    '<span class=tag>image: <b>' + P.w + '&times;' + P.h + '</b></span>' +
    '<span class=tag>channels: <b>R,G,B &rarr; UTF-8</b></span></div>' +
    '<div class=card style="margin-top:16px"><h2>the source, reconstructed from those pixels</h2>' +
    '<pre id=src></pre></div>' +
    '</div></body>';

  document.getElementById('src').textContent = SRC;

  /* Repaint the raw RGB stream onto a canvas and run a scanning highlight
     over it, so you can watch the code-as-image being read left to right. */
  var cv = document.getElementById('cv');
  cv.width = P.w; cv.height = P.h;
  var g = cv.getContext('2d'), img = g.createImageData(P.w, P.h), d = img.data, rgb = P.rgb;
  for (var i = 0, j = 0; i < P.w * P.h; i++) {
    d[i * 4] = rgb[j++]; d[i * 4 + 1] = rgb[j++]; d[i * 4 + 2] = rgb[j++]; d[i * 4 + 3] = 255;
  }
  var scan = 0;
  (function loop() {
    g.putImageData(img, 0, 0);
    g.fillStyle = 'rgba(138,180,248,0.55)';
    g.fillRect(0, scan % P.h, P.w, 1);
    g.fillStyle = 'rgba(138,180,248,0.12)';
    g.fillRect(0, 0, P.w, scan % P.h);
    scan = (scan + 1) % (P.h + 1);
    requestAnimationFrame(loop);
  })();
})();
