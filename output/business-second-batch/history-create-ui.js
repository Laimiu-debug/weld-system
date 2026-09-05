async(page)=>{
 const modal=page.getByRole('dialog',{name:'添加工作履历'});
 await modal.getByRole('textbox',{name:'* 公司名称',exact:true}).fill('F10 页面履历公司');
 await modal.getByRole('textbox',{name:'* 职位',exact:true}).fill('焊工');
 const start=modal.getByRole('textbox',{name:'* 工作时间',exact:true});
 await start.fill('2025-01-01');await start.press('Enter');
 const end=modal.getByRole('textbox',{name:'结束日期（可不填）',exact:true});
 await end.fill('2025-12-31');await end.press('Enter');
 await modal.getByRole('textbox',{name:'工作地点',exact:true}).fill('F10 车间');
 await modal.getByRole('button',{name:'OK',exact:true}).click();
 await page.getByText('F10 页面履历公司',{exact:true}).waitFor();
}
