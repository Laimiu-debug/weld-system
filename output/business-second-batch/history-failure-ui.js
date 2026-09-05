async(page)=>{
 const pattern=/\/api\/v1\/welders\/2\/work-histories\?/;
 await page.route(pattern,route=>route.fulfill({status:500,contentType:'application/json',body:'{"detail":"F10 本地故障测试"}'}));
 await page.reload();
 await page.getByText('工作履历加载失败，请重试',{exact:true}).waitFor();
 if(await page.getByText('暂无工作履历记录',{exact:true}).count())throw new Error('Failure shown as empty history');
 await page.screenshot({path:'output/playwright/f10-history-error.png',fullPage:true});
 await page.unroute(pattern);
 await page.getByRole('button',{name:'重 试',exact:true}).click();
 await page.getByText('暂无工作履历记录',{exact:true}).waitFor();
 await page.getByRole('button',{name:'plus 添加工作履历',exact:true}).click();
}
