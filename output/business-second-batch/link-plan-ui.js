async(page)=>{
 const row=page.getByRole('row').filter({has:page.getByRole('cell',{name:'F06 页面计划',exact:true})});
 await row.getByRole('button',{name:'关联任务',exact:true}).click();
 await page.getByRole('combobox',{name:'计划关联任务',exact:true}).click();
}
