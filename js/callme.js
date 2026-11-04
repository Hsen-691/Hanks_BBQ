/* "Call me" hand that flies out of the cart button with the Hala walla sound whenever an item is added.
   app.js calls window.callMeFX() at the same moment it plays the sound.

   The hand is the owner's real photo (img/callme-hand.png, a transparent cut-out). To swap the photo, replace that
   file with another transparent PNG. If the file is missing, a drawn hand is used instead. */
(function () {
  var HAND_IMAGE = "img/callme-hand.png";   // set to "" to always use the drawn hand

  var el = null, hand = null, photoOK = false;
  if (HAND_IMAGE) { var probe = new Image(); probe.onload = function () { photoOK = true; }; probe.src = HAND_IMAGE; }

  var HAND_SVG = `
<svg class="cm-hand" viewBox="0 0 360 440" aria-hidden="true">
  <defs>
    <linearGradient id="cmCyl" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#9a5d3a"/><stop offset=".15" stop-color="#c78c61"/><stop offset=".38" stop-color="#f0c6a0"/>
      <stop offset=".62" stop-color="#dba274"/><stop offset=".86" stop-color="#b87d54"/><stop offset="1" stop-color="#8f553a"/>
    </linearGradient>
    <linearGradient id="cmFist" x1=".1" x2=".9" y1="0" y2="1">
      <stop offset="0" stop-color="#ecbb92"/><stop offset=".5" stop-color="#d9a073"/><stop offset="1" stop-color="#b57a52"/>
    </linearGradient>
    <linearGradient id="cmNail" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#fbe3d8"/><stop offset=".7" stop-color="#efbfb0"/><stop offset="1" stop-color="#e2a495"/>
    </linearGradient>
    <linearGradient id="cmCuff" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#7a120c"/><stop offset=".3" stop-color="#d42a20"/><stop offset=".5" stop-color="#ea4b3d"/>
      <stop offset=".78" stop-color="#b81f16"/><stop offset="1" stop-color="#6e0f0a"/>
    </linearGradient>
    <linearGradient id="cmFade" x1="0" x2="0" y1="0" y2="1"><stop offset=".93" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
    <mask id="cmMask"><rect x="-40" y="0" width="440" height="440" fill="url(#cmFade)"/></mask>
    <filter id="cmB1" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.2"/></filter>
    <filter id="cmB3" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="3.5"/></filter>
    <filter id="cmGrain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="2" seed="7" result="n"/>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 .25  0 0 0 0 .13  0 0 0 0 .07  0 0 0 .55 -.12" result="g"/>
      <feComposite in="g" in2="SourceAlpha" operator="in" result="gi"/>
      <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="gi"/></feMerge>
    </filter>
    <filter id="cmAO" x="-25%" y="-25%" width="150%" height="150%"><feDropShadow dx="0" dy="2" stdDeviation="3.2" flood-color="#4a2514" flood-opacity=".55"/></filter>
  </defs>

  <g mask="url(#cmMask)">
    <!-- sleeve + wrist -->
    <path d="M112 296 C110 336 106 360 102 384 L258 384 C254 360 250 336 248 296Z" fill="url(#cmCyl)"/>
    <rect x="92" y="362" width="176" height="78" rx="10" fill="url(#cmCuff)"/>
    <rect x="92" y="380" width="176" height="9" fill="#f5eee3" opacity=".95"/>
    <rect x="92" y="396" width="176" height="9" fill="#f2c400"/>
    <path d="M92 364 H268" stroke="#3b0a06" stroke-opacity=".55" stroke-width="5" filter="url(#cmB1)"/>

    <g filter="url(#cmGrain)">
    <!-- little finger (behind the fist) -->
    <g transform="translate(264,176) rotate(26)" filter="url(#cmAO)">
      <rect x="-21" y="-66" width="42" height="128" rx="21" fill="url(#cmCyl)"/>
      <rect x="-12" y="-60" width="24" height="32" rx="10" fill="url(#cmNail)"/>
      <path d="M-8 -55 Q-2 -58 4 -57" stroke="#fff" stroke-opacity=".75" stroke-width="2.4" stroke-linecap="round" fill="none"/>
      <g fill="none" stroke="#7c4a2e" stroke-opacity=".5" stroke-linecap="round" stroke-width="1.8">
        <path d="M-11 -8 Q0 -4 11 -8"/><path d="M-10 -3 Q0 1 10 -3"/><path d="M-10 26 Q0 30 10 26"/>
      </g>
      <ellipse cx="-9" cy="-4" rx="3.2" ry="20" fill="#fff" opacity=".3" filter="url(#cmB1)"/>
    </g>

    <!-- thumb (behind the fist) -->
    <g transform="translate(84,284) rotate(-60)" filter="url(#cmAO)">
      <rect x="-27" y="-84" width="54" height="162" rx="27" fill="url(#cmCyl)"/>
      <rect x="-16" y="-78" width="32" height="40" rx="13" fill="url(#cmNail)"/>
      <path d="M-11 -72 Q-3 -76 6 -74" stroke="#fff" stroke-opacity=".75" stroke-width="2.6" stroke-linecap="round" fill="none"/>
      <g fill="none" stroke="#7c4a2e" stroke-opacity=".5" stroke-linecap="round" stroke-width="1.9">
        <path d="M-14 -14 Q0 -9 14 -14"/><path d="M-13 -7 Q0 -2 13 -7"/><path d="M-12 -28 Q0 -25 12 -28" stroke-opacity=".3"/>
      </g>
      <ellipse cx="-10" cy="-16" rx="3.4" ry="24" fill="#fff" opacity=".28" filter="url(#cmB1)"/>
    </g>

    <!-- fist block + thumb base -->
    <rect x="90" y="196" width="174" height="148" rx="60" fill="url(#cmFist)"/>
    <ellipse cx="120" cy="306" rx="56" ry="36" transform="rotate(30 120 306)" fill="url(#cmFist)" filter="url(#cmB1)"/>

    <!-- curled fingers: knuckle on top, fold in the middle, fingernail tucked at the bottom -->
    <g transform="rotate(3 230 200)" filter="url(#cmAO)">
      <rect x="204" y="144" width="52" height="124" rx="26" fill="url(#cmCyl)"/>
      <rect x="215" y="236" width="30" height="24" rx="10" fill="url(#cmNail)"/>
    </g>
    <g transform="rotate(-3 125 205)" filter="url(#cmAO)">
      <rect x="98" y="146" width="54" height="124" rx="27" fill="url(#cmCyl)"/>
      <rect x="110" y="238" width="30" height="24" rx="10" fill="url(#cmNail)"/>
    </g>
    <g filter="url(#cmAO)">
      <rect x="148" y="128" width="58" height="140" rx="29" fill="url(#cmCyl)"/>
      <rect x="162" y="238" width="30" height="24" rx="10" fill="url(#cmNail)"/>
    </g>

    <!-- shadow where the nails press into the palm, and the deep fold of each finger -->
    <g fill="none" stroke="#5e3220" stroke-linecap="round">
      <path d="M104 232 Q125 244 148 232" stroke-width="4" stroke-opacity=".55" filter="url(#cmB1)"/>
      <path d="M155 230 Q177 243 201 230" stroke-width="4" stroke-opacity=".55" filter="url(#cmB1)"/>
      <path d="M209 232 Q231 244 252 232" stroke-width="4" stroke-opacity=".55" filter="url(#cmB1)"/>
      <path d="M102 268 Q124 282 148 270" stroke-width="6" stroke-opacity=".5" filter="url(#cmB1)"/>
      <path d="M154 268 Q177 282 202 268" stroke-width="6" stroke-opacity=".5" filter="url(#cmB1)"/>
      <path d="M208 268 Q231 282 253 268" stroke-width="6" stroke-opacity=".5" filter="url(#cmB1)"/>
    </g>
    <!-- joint creases -->
    <g fill="none" stroke="#6f4128" stroke-opacity=".55" stroke-linecap="round" stroke-width="1.9">
      <path d="M110 178 Q125 185 140 178"/><path d="M112 185 Q125 191 138 185"/>
      <path d="M161 162 Q177 170 193 162"/><path d="M163 169 Q177 176 191 169"/>
      <path d="M214 174 Q229 181 244 174"/><path d="M216 181 Q229 187 242 181"/>
      <path d="M108 214 Q125 221 142 214" stroke-width="2.4"/><path d="M159 212 Q177 220 195 212" stroke-width="2.4"/><path d="M213 214 Q230 221 247 214" stroke-width="2.4"/>
      <path d="M112 221 Q125 226 138 221" stroke-opacity=".35"/><path d="M164 219 Q177 225 190 219" stroke-opacity=".35"/><path d="M218 221 Q230 226 242 221" stroke-opacity=".35"/>
    </g>
    <!-- knuckle blush and light catching the knuckles -->
    <g filter="url(#cmB3)">
      <ellipse cx="125" cy="160" rx="16" ry="10" fill="#c4614a" opacity=".16"/><ellipse cx="177" cy="144" rx="17" ry="10" fill="#c4614a" opacity=".16"/><ellipse cx="230" cy="157" rx="16" ry="10" fill="#c4614a" opacity=".16"/>
      <ellipse cx="119" cy="176" rx="6" ry="17" fill="#fff" opacity=".33"/><ellipse cx="169" cy="162" rx="7" ry="19" fill="#fff" opacity=".4"/><ellipse cx="221" cy="172" rx="6" ry="16" fill="#fff" opacity=".32"/>
    </g>
    <!-- soft shade on the lower fist -->
    <path d="M112 318 Q176 358 250 316 L252 344 L108 344Z" fill="#5a2f1b" opacity=".35" filter="url(#cmB3)"/>
    </g>
  </g>

  <!-- ring-ring marks -->
  <g class="cm-ring a"><path d="M2 196 Q-10 214 -4 238"/><path d="M-14 182 Q-32 212 -20 248"/></g>
  <g class="cm-ring b"><path d="M322 92 Q338 108 334 132"/><path d="M336 76 Q360 104 350 144"/></g>
</svg>`;

  var PHOTO_RINGS = '<svg viewBox="0 0 560 544" aria-hidden="true">' +
    '<g class="cm-ring a"><path d="M8 24 Q-14 52 -6 92"/><path d="M-12 6 Q-44 52 -24 112"/></g>' +
    '<g class="cm-ring b"><path d="M574 44 Q596 78 588 122"/><path d="M590 24 Q626 72 610 140"/></g></svg>';

  function build() {
    el = document.createElement("div");
    el.className = "callme";
    el.setAttribute("aria-hidden", "true");
    var photo = HAND_IMAGE && photoOK;
    el.dataset.mode = photo ? "photo" : "svg";
    el.innerHTML = (photo ? '<div class="cm-hand cm-photo"><span class="cm-pic"><img src="' + HAND_IMAGE + '" alt=""></span>' + PHOTO_RINGS + '</div>' : HAND_SVG) + '<div class="cm-bubble"></div>';
    document.body.appendChild(el);
    hand = el.querySelector(".cm-hand");
  }

  /* park the hand just under the cart button and work out where it flies out from */
  function place(cart) {
    var cr = cart.getBoundingClientRect();
    var vw = document.documentElement.clientWidth;
    var onRight = cr.left + cr.width / 2 > vw / 2;
    el.classList.toggle("side-r", onRight);
    el.classList.toggle("side-l", !onRight);
    var bar = document.getElementById("topbar");            // phones have two header rows, so sit under the whole header
    var below = Math.max(cr.bottom, bar ? bar.getBoundingClientRect().bottom : 0);
    el.style.top = Math.round(below + 6) + "px";
    var room = el.dataset.mode === "photo" ? 24 : 0;          // the photo swings wider when it wags, keep it off the screen edge
    if (onRight) { el.style.right = Math.max(6, Math.round(vw - cr.right - 6)) + room + "px"; el.style.left = "auto"; }
    else { el.style.left = Math.max(6, Math.round(cr.left - 6)) + room + "px"; el.style.right = "auto"; }
    var er = el.getBoundingClientRect(), hr = hand.getBoundingClientRect();
    var hx = hr.left + hr.width / 2, hy = hr.top + hr.height / 2;
    el.style.setProperty("--ox", Math.round(hx - er.left) + "px");
    el.style.setProperty("--oy", Math.round(hy - er.top) + "px");
    el.style.setProperty("--dx", Math.round(cr.left + cr.width / 2 - hx) + "px");
    el.style.setProperty("--dy", Math.round(cr.top + cr.height / 2 - hy) + "px");
  }

  function restart(node, cls) {
    node.classList.remove(cls);
    void node.offsetWidth;        // lets the animation start over if it is already running
    node.classList.add(cls);
  }

  window.callMeFX = function () {
    if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    var cart = document.getElementById("cartBtn");
    if (!cart) return;
    if (el && el.dataset.mode === "svg" && HAND_IMAGE && photoOK) { el.remove(); el = null; }   // the photo finished loading, use it
    if (!el) build();
    var ar = typeof Lang !== "undefined" && Lang.isAr;
    el.querySelector(".cm-bubble").innerHTML = ar ? "هلا <b>والله!</b>" : "Hala <b>walla!</b>";
    el.classList.remove("go");
    place(cart);
    restart(el, "go");
    restart(cart, "ringing");
  };
})();