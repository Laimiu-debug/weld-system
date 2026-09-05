async(page)=>{
 await page.getByRole('dialog').getByRole('button',{name:'Close',exact:true}).click();
 const pattern=/\/api\/v1\/materials\/transactions\?/;
 await page.route(pattern,route=>route.fulfill({status:500,contentType:'application/json',body:'{"detail":"F05 流水故障"}'}));
 await page.getByRole('button',{name:'库存流水',exact:true}).click();
 await page.getByText('无法加载库存流水，请重试',{exact:true}).waitFor();
 await page.unroute(pattern);
 await page.getByRole('button',{name:'重试',exact:true}).click();
 await page.getByRole('cell',{name:'-3 kg',exact:true}).waitFor();
 await page.screenshot({path:'output/playwright/f05-personal-history.png',fullPage:true});
 await page.getByRole('dialog').getByRole('button',{name:'Close',exact:true}).click();
 const downloadPromise=page.waitForEvent('download');
 await page.getByRole('button',{name:'download 导出信息'}).click();
 await (await downloadPromise).saveAs('output/playwright/f05-personal.csv');
 await page.getByRole('button',{name:'删除焊材',exact:true}).click();
}
