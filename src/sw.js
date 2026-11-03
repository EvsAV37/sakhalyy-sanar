/* Сахалыы саҥар — офлайн-работа и обновления */
const VERSION='/*VERSION*/';
/* AUDIO_FILES — индекс озвучки (какой файл у какой фразы). Сами MP3 (папка a/) кладёт в кеш «audio-mp3» страница,
   в фоне и с показом процента; здесь они только отдаются из кеша. */
const AUDIO=/*AUDIO_FILES*/[];
const CORE=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./icon-maskable-512.png','./apple-touch-icon.png'].concat(/*FONT_FILES*/[],AUDIO);
const CORE_CACHE='core-'+VERSION;
self.addEventListener('install',e=>{e.waitUntil(caches.open(CORE_CACHE).then(c=>c.addAll(CORE.map(u=>new Request(u,{cache:'reload'})))))});
self.addEventListener('activate',e=>{e.waitUntil((async()=>{
  for(const k of await caches.keys())
    // прежние версии; «audio» и «fonts» — кеши старых сборок (озвучка в base64, Google Fonts)
    if((k.startsWith('core-')&&k!==CORE_CACHE)||k==='audio'||k==='fonts')await caches.delete(k);
  await self.clients.claim();
})())});
self.addEventListener('message',e=>{if(e.data==='skip')self.skipWaiting()});
self.addEventListener('fetch',e=>{
  const req=e.request;if(req.method!=='GET')return;
  const url=new URL(req.url);
  if(url.origin!==location.origin)return;
  if(req.mode==='navigate'){e.respondWith(caches.match('./index.html').then(r=>r||fetch(req)));return}
  e.respondWith(caches.match(req,{ignoreSearch:true}).then(r=>r||fetch(req)));
});
