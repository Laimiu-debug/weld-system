async(page)=>{
 const modal=page.getByRole('dialog',{name:'焊材出库'});
 await modal.getByRole('spinbutton',{name:'* 出库数量',exact:true}).fill('100');
 await modal.getByRole('textbox',{name:'* 去向',exact:true}).fill('F05 车间');
 await modal.getByRole('button',{name:/OK$/}).click();
 await page.getByText('出库数量不能超过当前库存（15 kg）',{exact:true}).waitFor();
 await modal.getByRole('spinbutton',{name:'* 出库数量',exact:true}).fill('3');
 await page.route(/\/api\/v1\/materials\/stock-out\?/,route=>route.fulfill({status:500,contentType:'application/json',body:'{"detail":"F05 故障测试"}'}),{times:1});
 await modal.getByRole('button',{name:/OK$/}).click();
 await page.getByText('出库失败，请重试，已保留当前输入',{exact:true}).waitFor();
 if(Number(await modal.getByRole('spinbutton',{name:'* 出库数量',exact:true}).inputValue())!==3)throw new Error('Lost out input');
 await modal.getByRole('button',{name:/OK$/}).click();
 await page.getByRole('cell',{name:'12 kg',exact:true}).waitFor();
 await page.route(/\/api\/v1\/materials\/transactions\?/,route=>route.fulfill({status:500,contentType:'application/json',body:'{"detail":"F05 流水故障"}'}),{times:1});
 await page.getByRole('button',{name:'库存流水',exact:true}).click();
 await page.getByText('无法加载库存流水，请重试',{exact:true}).waitFor();
 await page.getByRole('button',{name:'重试',exact:true}).click();
 await page.getByRole('cell',{name:'-3 kg',exact:true}).waitFor();
 if(await page.getByText('--3 kg',{exact:true}).count())throw new Error('Double negative quantity');
 await page.screenshot({path:'output/materials-first-batch/personal-history.png',fullPage:true});
}
