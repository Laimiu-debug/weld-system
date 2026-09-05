async(page)=>{
 await page.getByRole('dialog',{name:'运行结果'}).getByRole('cell',{name:'completed',exact:true}).waitFor();
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'导出 CSV',exact:true}).click();
 await (await download).saveAs('output/playwright/f09-report.csv');
 await page.screenshot({path:'output/playwright/f09-report.png',fullPage:true});
 await page.getByRole('button',{name:'关 闭',exact:true}).click();
 await page.goto('http://127.0.0.1:5173/quality/2');
}
