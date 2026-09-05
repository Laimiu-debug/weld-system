async (page) => {
 await page.getByRole('button',{name:'继续填写',exact:true}).click();
 await page.getByRole('textbox',{name:'备注',exact:true}).fill('F05 失败后保留的输入');
 await page.route(/\/api\/v1\/materials\/\?/, route => route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({success:false,message:'F05 模拟保存失败'})}),{times:1});
 await page.getByRole('button',{name:'save 添加焊材'}).click();
 await page.getByText('保存失败，请检查填写内容后重试，已保留当前输入',{exact:true}).waitFor();
 if(await page.getByRole('textbox',{name:'备注',exact:true}).inputValue()!=='F05 失败后保留的输入') throw new Error('Input was lost');
 if(!page.url().endsWith('/create')) throw new Error('Navigated after failure');
 await page.getByRole('button',{name:'save 添加焊材'}).click();
 await page.waitForURL(/\/materials\/\d+$/);
 await page.getByRole('heading',{name:'焊材详情'}).waitFor();
 await page.screenshot({path:'output/materials-first-batch/personal-detail.png',fullPage:true});
 console.log({create:true,preview:true,failedSaveRetainsInput:true,url:page.url()});
}
