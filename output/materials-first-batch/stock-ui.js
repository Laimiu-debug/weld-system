async(page)=>{
 const modal=page.getByRole('dialog',{name:'焊材入库'});
 await modal.getByRole('spinbutton',{name:'* 入库数量',exact:true}).fill('5');
 await page.route(/\/api\/v1\/materials\/stock-in\?/,route=>route.fulfill({status:200,contentType:'application/json',body:'{"success":false}'}),{times:1});
 await modal.getByRole('button',{name:'OK',exact:true}).click();
 await page.getByText('入库失败，请重试，已保留当前输入',{exact:true}).waitFor();
 if(Number(await modal.getByRole('spinbutton',{name:'* 入库数量',exact:true}).inputValue())!==5)throw new Error('Lost stock input');
 await modal.getByRole('button',{name:'OK',exact:true}).click();
 await page.getByRole('cell',{name:'15 kg',exact:true}).waitFor();
 await page.getByRole('button',{name:'出 库',exact:true}).click();
}
