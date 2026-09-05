async(page)=>{
 const endpoint={'/production/plans':'/production/plans','/quality/standards':'/quality/standards','/employees/performance':'/employees/performances','/reports/custom':'/reports/templates'}[page.url().replace('http://127.0.0.1:5173','')];
 if(!endpoint)throw new Error('Unknown search page');
 const box=page.getByRole('searchbox');
 const matching=(r,term)=>r.url().includes('/api/v1'+endpoint+'?')&&(r.url().match(/[?&]search=([^&]*)/)?.[1]||null)===term;
 const search=async term=>{const response=page.waitForResponse(r=>matching(r,term||null));await box.fill(term);await box.press('Enter');if(!(await response).ok())throw new Error('Search API failed');};
 await search('F04_ALPHA');
 await page.getByRole('cell',{name:'F04_ALPHA',exact:true}).first().waitFor();
 if(await page.getByRole('cell',{name:'F04_BETA',exact:true}).count())throw new Error('Old query used');
 await search('F04_BETA');
 await page.getByRole('cell',{name:'F04_BETA',exact:true}).first().waitFor();
 await search('F04_BETA');
 await search('');
 await page.getByRole('cell',{name:'F04_ALPHA',exact:true}).first().waitFor();
 let release,arrived;
 const held=new Promise(resolve=>release=resolve),ready=new Promise(resolve=>arrived=resolve);
 const pattern=new RegExp('/api/v1'+endpoint+'\\?');
 await page.route(pattern,async route=>{if((route.request().url().match(/[?&]search=([^&]*)/)?.[1]||null)==='F04_ALPHA'){const response=await route.fetch();arrived();await held;await route.fulfill({response});}else await route.continue();});
 await box.fill('F04_ALPHA');await box.press('Enter');await ready;
 await search('F04_BETA');
 await page.getByRole('cell',{name:'F04_BETA',exact:true}).first().waitFor();
 const late=page.waitForResponse(r=>matching(r,'F04_ALPHA'));release();await (await late).finished();
 await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 if(await page.getByRole('cell',{name:'F04_ALPHA',exact:true}).count())throw new Error('Late response replaced current search');
 await page.getByRole('cell',{name:'F04_BETA',exact:true}).first().waitFor();
 await page.unroute(pattern);
 await page.screenshot({path:'output/playwright/f04-'+endpoint.replaceAll('/','-')+'.png',fullPage:true});
}
