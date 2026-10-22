const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1400,height:900}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  try{
    await page.goto('http://127.0.0.1:8765/docs/');
    await page.locator('#search').fill('empleo');
    await page.locator('#apply').click();
    assert.match(await page.locator('#count').innerText(),/1 señales/);
    await page.locator('[data-id="SIG-02"]').click();
    await page.locator('#brief-now').click();
    await page.locator('#generate').click();
    assert.match(await page.locator('#brief-text').innerText(),/Brief ejecutivo/);
    await page.locator('[data-view="radar"]').click();
    await page.locator('#search').fill('nada-coincide-z999');
    await page.locator('#apply').click();
    assert.match(await page.locator('#detail').innerText(),/No hay señales/);
    await page.locator('#clear').click();
    assert.match(await page.locator('#count').innerText(),/5 señales/);
    await fs.promises.mkdir('test-results',{recursive:true});
    await page.screenshot({path:'test-results/media-copilot.png',fullPage:true});
    assert.deepEqual(errors,[]);
    console.log('Media Copilot: demo interactiva OK');
  } finally {await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
