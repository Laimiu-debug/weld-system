async(page)=>{
 const modal=page.getByRole('dialog',{name:'新建绩效'});
 const period=modal.getByRole('textbox',{name:'* 考核周期',exact:true});
 await period.fill('2026-Q5');
 await modal.getByRole('button',{name:'OK',exact:true}).click();
 await page.getByText('请输入 YYYY-MM 或 YYYY-Q1 至 YYYY-Q4',{exact:true}).waitFor();
 await period.fill('2026-Q3');
 await modal.getByRole('spinbutton',{name:'总分',exact:true}).fill('82');
 await page.route(/\/api\/v1\/employees\/performances\?/,route=>route.fulfill({status:200,contentType:'application/json',body:'{"success":false,"message":"F08 测试保存失败"}'}),{times:1});
 await modal.getByRole('button',{name:'OK',exact:true}).click();
 await page.getByText('F08 测试保存失败',{exact:true}).waitFor();
 if(await period.inputValue()!=='2026-Q3')throw new Error('Lost performance form input');
 const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/employees/performances?'));
 await modal.getByRole('button',{name:/OK$/}).click();
 if(!(await response).ok())throw new Error('Performance create failed');
 await page.getByRole('cell',{name:'2026-Q3',exact:true}).waitFor();
 await page.screenshot({path:'output/playwright/f08-performance.png',fullPage:true});
}
