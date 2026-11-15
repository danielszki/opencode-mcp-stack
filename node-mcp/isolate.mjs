import { chromium } from 'playwright';
const b = await chromium.launch({ executablePath: '/usr/bin/chromium' });
const p = await b.newPage();
const hits = [];
p.on('response', r => { if (r.url().includes('/g/collect')) hits.push(decodeURIComponent(r.url()).match(/[?&]en=([^&]+)/)?.[1]); });
await p.setContent(`<!doctype html><html><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-N9ENQTNL81"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','G-N9ENQTNL81',{debug_mode:true});</script>
</head><body><h1>teste isolado</h1></body></html>`, { waitUntil: 'load' });
await p.waitForTimeout(6000);
await p.evaluate(() => window.gtag('event','isolated_probe',{debug_mode:true}));
await p.waitForTimeout(5000);
console.log('hits:', JSON.stringify(hits));
await b.close();
