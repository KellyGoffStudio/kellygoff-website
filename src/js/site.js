// open every page at the top (unless the visitor used Back/Forward)
(function(){
  var nav=(performance.getEntriesByType&&performance.getEntriesByType('navigation')[0])||{};
  if(nav.type==='back_forward'||location.hash)return;
  if('scrollRestoration' in history)history.scrollRestoration='manual';
  function top(){window.scrollTo(0,0);var h=document.querySelector('.site-head');if(h&&h.scrollIntoView)h.scrollIntoView({block:'start'});}
  top();
  window.addEventListener('load',top);
  window.addEventListener('pageshow',function(e){if(!e.persisted)top();});
})();
(function(){
  // mobile menu
  var mb=document.querySelector('.menu-btn'), nav=document.getElementById('nav');
  if(mb&&nav){
    mb.addEventListener('click',function(){var o=nav.classList.toggle('open');mb.setAttribute('aria-expanded',o?'true':'false');mb.textContent=o?'Close':'Menu';});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&nav.classList.contains('open')){mb.click();mb.focus();}});
  }
  // lightbox
  var items=[].slice.call(document.querySelectorAll('[data-lb]'));
  var dlg=document.getElementById('lb');
  if(items.length&&dlg){
    var img=dlg.querySelector('img'),cap=dlg.querySelector('.lb-cap'),i=0;
    function show(n){i=(n+items.length)%items.length;var b=items[i];img.src=b.getAttribute('data-lb');img.alt=b.getAttribute('data-alt')||'';cap.textContent=(b.getAttribute('data-cap')||'')+'  ·  '+(i+1)+' / '+items.length;}
    items.forEach(function(b,n){b.addEventListener('click',function(){show(n);if(dlg.showModal)dlg.showModal();else dlg.setAttribute('open','');});});
    dlg.querySelector('.x').addEventListener('click',function(){dlg.close();});
    dlg.querySelector('.pv').addEventListener('click',function(){show(i-1);});
    dlg.querySelector('.nx').addEventListener('click',function(){show(i+1);});
    dlg.addEventListener('keydown',function(e){if(e.key==='ArrowLeft')show(i-1);if(e.key==='ArrowRight')show(i+1);});
    dlg.addEventListener('click',function(e){if(e.target===dlg)dlg.close();});
  }
})();
// click-to-load video (only on http/https; from a local file the link opens YouTube instead)
(function(){
  var v=document.querySelector('.video.yt');
  if(!v||location.protocol.indexOf('http')!==0)return;
  v.querySelector('a').addEventListener('click',function(e){
    e.preventDefault();
    var f=document.createElement('iframe');
    f.src='https://www.youtube-nocookie.com/embed/'+v.getAttribute('data-id')+'?autoplay=1&rel=0&start='+(v.getAttribute('data-start')||0);
    f.title='Video: public work and process';f.allow='autoplay; fullscreen; picture-in-picture';f.allowFullscreen=true;
    v.innerHTML='';v.appendChild(f);
  });
})();
