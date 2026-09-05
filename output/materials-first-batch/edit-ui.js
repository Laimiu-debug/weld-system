async(page)=>{
 await page.getByRole('button',{name:'edit 编辑焊材'}).click();
 await page.getByRole('textbox',{name:'* 焊材名称',exact:true}).fill('F05 页面修改后焊丝');
 await page.getByRole('button',{name:'right 下一步'}).click();
 if(!await page.getByRole('spinbutton',{name:'* 当前库存',exact:true}).isDisabled())throw new Error('Stock editable');
 if(!await page.getByRole('combobox',{name:'* 单位',exact:true}).isDisabled())throw new Error('Unit editable');
 await page.getByRole('button',{name:'right 下一步'}).click();
 await page.getByRole('button',{name:'right 下一步'}).click();
 const responsePromise=page.waitForResponse(r=>r.request().method()==='PUT'&&r.url().includes('/materials/'));
 await page.getByRole('button',{name:'save 保存修改'}).click();
 const response=await responsePromise;
 const body=response.request().postDataJSON();
 if('current_stock' in body||'unit' in body)throw new Error('Edit sent inventory fields');
 if(!response.ok())throw new Error('Edit failed');
 await page.waitForURL(/\/materials\/\d+$/);
 await page.getByRole('cell',{name:'10 kg',exact:true}).waitFor();
 await page.getByRole('button',{name:'入 库',exact:true}).click();
}
