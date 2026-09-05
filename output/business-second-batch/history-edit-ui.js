async(page)=>{
 const modal=page.getByRole('dialog',{name:'编辑工作履历'});
 await modal.getByRole('textbox',{name:'* 职位',exact:true}).fill('高级焊工');
 await modal.getByRole('checkbox',{name:'仍在职（不填写结束日期）'}).check();

 const response=page.waitForResponse(r=>r.request().method()==='PUT'&&r.url().includes('/work-histories/'));
 await modal.getByRole('button',{name:'OK',exact:true}).click();
 const body=await (await response).json();
 if(body.data.end_date!==null)throw new Error('End date was not cleared');
 await page.getByText('高级焊工',{exact:true}).waitFor();
 await page.getByText('至今',{exact:true}).waitFor();
}
