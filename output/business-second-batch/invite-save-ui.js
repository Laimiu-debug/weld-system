async(page)=>{
 const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/enterprise/invitations'));
 await page.getByRole('dialog',{name:'发送邀请'}).getByRole('button',{name:'OK',exact:true}).click();
 const body=await (await response).json();
 if(body.data?.email_sent!==false || !body.data?.invite_url)throw new Error('Invitation result mismatch');
 await page.getByText('邀请已创建，但邮件未发出；请在邀请详情复制链接交给对方',{exact:true}).waitFor();
 await page.screenshot({path:'output/playwright/f11-invitation-warning.png'});
}
