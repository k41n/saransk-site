/* Страница «Было / Стало»: режимы, вкладки, масштаб iframe, панель. */
(function () {
  var stage = document.getElementById('stage');
  if (!stage) return;
  var panel = document.getElementById('panel');
  var frameNew = document.getElementById('frame-new');
  var demo = document.getElementById('demo');
  var oldImg = document.getElementById('old-img');
  var modeBtns = document.querySelectorAll('[data-mode]');
  var tabBtns = document.querySelectorAll('[data-tab]');
  var toggle = document.getElementById('panel-toggle');

  function store(key, value) {
    try { sessionStorage.setItem(key, value); } catch (e) {}
  }
  function load(key) {
    try { return sessionStorage.getItem(key); } catch (e) { return null; }
  }

  // Логическая ширина демо: 1280 px на компьютере, 390 px на телефоне.
  function layout() {
    var logical = stage.getAttribute('data-mode') === 'phone' ? 390 : 1280;
    var w = frameNew.clientWidth;
    var h = frameNew.clientHeight;
    if (!w || !h) return;
    var s = Math.min(1, w / logical);
    demo.style.width = logical + 'px';
    demo.style.height = (h / s) + 'px';
    demo.style.transform = 'scale(' + s + ')';
    demo.style.left = Math.max(0, (w - logical * s) / 2) + 'px';
  }

  function press(buttons, attr, value) {
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('aria-pressed', buttons[i].getAttribute(attr) === value ? 'true' : 'false');
    }
  }

  function setMode(mode) {
    stage.setAttribute('data-mode', mode);
    oldImg.src = oldImg.getAttribute('data-' + mode);
    press(modeBtns, 'data-mode', mode);
    store('cmpMode', mode);
    document.querySelector('.frame-old').scrollTop = 0;
    layout();
  }

  function setTab(tab) {
    stage.setAttribute('data-tab', tab);
    press(tabBtns, 'data-tab', tab);
    layout();
  }

  for (var i = 0; i < modeBtns.length; i++) {
    modeBtns[i].addEventListener('click', function () { setMode(this.getAttribute('data-mode')); });
  }
  for (var j = 0; j < tabBtns.length; j++) {
    tabBtns[j].addEventListener('click', function () { setTab(this.getAttribute('data-tab')); });
  }

  toggle.addEventListener('click', function () {
    var collapsed = panel.classList.toggle('collapsed');
    toggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    toggle.textContent = collapsed ? 'Развернуть панель' : 'Свернуть панель';
    store('cmpPanel', collapsed ? '1' : '0');
    layout();
  });

  if (window.ResizeObserver) {
    new ResizeObserver(layout).observe(frameNew);
  }
  window.addEventListener('resize', layout);

  if (load('cmpPanel') === '1') toggle.click();
  // Адрес вида compare.html#phone или #phone,new задаёт режим и вкладку.
  var hash = location.hash;
  var startMode = hash.indexOf('phone') >= 0 ? 'phone' : hash.indexOf('desktop') >= 0 ? 'desktop' : load('cmpMode');
  setMode(startMode === 'phone' ? 'phone' : 'desktop');
  if (hash.indexOf('new') >= 0) setTab('new');
  layout();
})();
