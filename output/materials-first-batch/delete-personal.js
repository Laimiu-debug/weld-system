async(page)=>{
 await page.route(/\/api\/v1\/materials\/6\?/,route=>route.fulfill({status:200,contentType:'application/json',body:'{"success":false}'}),{times:1});
 await page.getByRole('dialog').getByRole('button',{name:/删 除$/}).click();
 await page.getByText('删除失败，请重试，焊材资料仍保留',{exact:true}).waitFor();
 if(!page.url().endsWith('/6'))throw new Error('Navigated after failed delete');
 await page.getByRole('dialog').getByRole('button',{name:/删 除$/}).click();
 await page.waitForURL(/\/materials$/);
 await page.evaluate(()=>localStorage.clear());
 await page.goto('http://127.0.0.1:5173/login');
}
