async(page)=>{
 if(!page.url().endsWith('/quality/create'))throw new Error('Submitted before save');
 const pending=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/quality/inspections?'));
 await page.getByRole('button',{name:'save 保存检验记录',exact:true}).click();
 const response=await pending,body=await response.json();
 if(!response.ok()||body.data.standard_snapshot.version!=='2.0')throw new Error('Snapshot missing from saved inspection');
 await page.waitForURL(/\/quality$/);
 await page.goto('http://127.0.0.1:5173/welders/2');
}
