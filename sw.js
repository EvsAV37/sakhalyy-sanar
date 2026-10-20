/* Сахалыы саҥар — офлайн-работа и обновления */
const VERSION='d1ebfd0f4a';
const CORE=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./icon-maskable-512.png','./apple-touch-icon.png'].concat(["./fonts/onest-cyrillic-ext.woff2", "./fonts/onest-cyrillic.woff2", "./fonts/onest-latin.woff2", "./fonts/pt-serif-cyrillic-400-normal.woff2", "./fonts/pt-serif-cyrillic-ext-400-normal.woff2", "./fonts/pt-serif-latin-400-normal.woff2"]);
const AUDIO=["audio-00491a144b.json", "audio-7944366193.json", "audio-aa9c60e7de.json", "audio-c260ae22d3.json"];
const CORE_CACHE='core-'+VERSION, AUDIO_CACHE='audio', FONT_CACHE='fonts';
self.addEventListener('install',e=>{e.waitUntil((async()=>{
  const c=await caches.open(CORE_CACHE);await c.addAll(CORE.map(u=>new Request(u,{cache:'reload'})));
  const a=await caches.open(AUDIO_CACHE);
  for(const f of AUDIO){if(!(await a.match(f)))await a.add(new Request(f,{cache:'reload'}))}
})())});
self.addEventListener('activate',e=>{e.waitUntil((async()=>{
  for(const k of await caches.keys())if(k.startsWith('core-')&&k!==CORE_CACHE)await caches.delete(k);
  const a=await caches.open(AUDIO_CACHE);
  for(const r of await a.keys()){const n=new URL(r.url).pathname.split('/').pop();if(!AUDIO.includes(n))await a.delete(r)}
  await self.clients.claim();
})())});
self.addEventListener('message',e=>{if(e.data==='skip')self.skipWaiting()});
self.addEventListener('fetch',e=>{
  const req=e.request;if(req.method!=='GET')return;
  const url=new URL(req.url);
  if(url.hostname==='fonts.googleapis.com'||url.hostname==='fonts.gstatic.com'){
    e.respondWith(caches.open(FONT_CACHE).then(async c=>{const hit=await c.match(req);
      const net=fetch(req).then(r=>{if(r&&(r.ok||r.type==='opaque'))c.put(req,r.clone());return r}).catch(()=>hit);
      return hit||net}));return}
  if(url.origin!==location.origin)return;
  if(req.mode==='navigate'){e.respondWith(caches.match('./index.html').then(r=>r||fetch(req)));return}
  e.respondWith(caches.match(req,{ignoreSearch:true}).then(r=>r||fetch(req)));
});
