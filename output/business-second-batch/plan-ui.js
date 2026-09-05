async(page)=>{
 const modal=page.getByRole('dialog',{name:'新建生产计划'});
 await modal.getByRole('textbox',{name:'* 计划编号',exact:true}).fill('F06-UI-PLAN');
 await modal.getByRole('textbox',{name:'* 计划名称',exact:true}).fill('F06 页面计划');
 const start=modal.getByRole('textbox',{name:'* 开始日期',exact:true});
 const end=modal.getByRole('textbox',{name:'* 结束日期',exact:true});
 await start.fill('2026-09-01');await start.press('Enter');
 await end.fill('2026-08-01');await end.press('Enter');
 await modal.getByRole('button',{name:'OK',exact:true}).click();
 await page.getByText('结束日期不能早于开始日期',{exact:true}).waitFor();
 await end.fill('2026-09-04');await end.press('Enter');
 const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/production/plans?'));
 await modal.getByRole('button',{name:'OK',exact:true}).click();
 if(!(await response).ok())throw new Error('Plan create failed');
 await page.getByRole('cell',{name:'F06 页面计划',exact:true}).waitFor();
 const row=page.getByRole('row').filter({has:page.getByRole('cell',{name:'F06 页面计划',exact:true})});
 await row.getByRole('button',{name:'关联任务',exact:true}).click();
}
